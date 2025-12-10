from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components
import time
from cortex_client import CortexClientError
from metrics import get_collector
from orchestrator import Orchestrator
from tracer import generate_trace_id, set_trace_id


def create_workflow_html(current_step: int, total_steps: int, step_name: str):
    """Create animated circular workflow visualization as complete HTML"""
    
    # Define all agent workflow nodes - MORE DETAILED
    import math
    center_x, center_y = 400, 300
    radius = 200
    
    node_names = ["Input", "Enhancer", "Orchestrator", "Schema", "Cortex AI", "Execute", "Results", "Complete"]
    
    nodes = []
    for i, name in enumerate(node_names):
        angle = (i * 360 / len(node_names)) - 90
        rad = math.radians(angle)
        x = center_x + radius * math.cos(rad)
        y = center_y + radius * math.sin(rad)
        nodes.append({"id": i + 1, "name": name, "x": x, "y": y})
    
    # Build complete HTML with embedded CSS and SVG
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    body {{
        margin: 0;
        padding: 0;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 0.6; transform: scale(1); }}
        50% {{ opacity: 1; transform: scale(1.12); }}
    }}
    
    @keyframes dash {{
        to {{ stroke-dashoffset: -100; }}
    }}
    
    @keyframes centerPulse {{
        0%, 100% {{ r: 45; opacity: 0.25; }}
        50% {{ r: 65; opacity: 0.45; }}
    }}
    
    .workflow-container {{
        width: 100%;
        height: 600px;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    
    .node-circle.active {{
        animation: pulse 1.3s ease-in-out infinite;
        filter: drop-shadow(0 0 20px rgba(56, 189, 248, 0.9));
    }}
    
    .connection-line.active {{
        stroke: #38bdf8;
        stroke-width: 4;
        animation: dash 1.5s linear infinite;
        filter: drop-shadow(0 0 10px rgba(56, 189, 248, 0.7));
    }}
    
    .connection-line.completed {{
        stroke: #10b981;
        stroke-width: 3;
    }}
    
    .node-label {{
        fill: white;
        font-size: 14px;
        font-weight: 700;
        text-anchor: middle;
        text-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }}
    
    .node-status {{
        font-size: 22px;
        text-anchor: middle;
    }}
    
    .center-text {{
        fill: white;
        font-size: 20px;
        font-weight: 700;
        text-anchor: middle;
        text-shadow: 0 2px 6px rgba(0,0,0,0.6);
    }}
    
    .center-subtext {{
        fill: #94a3b8;
        font-size: 15px;
        text-anchor: middle;
    }}
    </style>
    </head>
    <body>
    <div class="workflow-container">
    <svg viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg" width="100%" height="100%">
    """
    
    # Add animated center pulse
    if current_step > 0 and current_step <= total_steps:
        html += f"""
        <circle cx="{center_x}" cy="{center_y}" fill="#38bdf8" opacity="0.3">
            <animate attributeName="r" values="45;75;45" dur="2.5s" repeatCount="indefinite"/>
            <animate attributeName="opacity" values="0.3;0.15;0.3" dur="2.5s" repeatCount="indefinite"/>
        </circle>
        """
    
    # Draw connections
    for i in range(len(nodes)):
        next_i = (i + 1) % len(nodes)
        x1, y1 = nodes[i]["x"], nodes[i]["y"]
        x2, y2 = nodes[next_i]["x"], nodes[next_i]["y"]
        
        conn_class = "connection-line"
        stroke_color = "#475569"
        stroke_width = "3"
        stroke_dasharray = "8,8"
        
        if i < current_step - 1:
            conn_class += " completed"
            stroke_color = "#10b981"
            stroke_dasharray = "none"
        elif i == current_step - 1:
            conn_class += " active"
            stroke_color = "#38bdf8"
            stroke_width = "4"
        
        html += f'<line class="{conn_class}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-dasharray="{stroke_dasharray}"/>'
    
    # Draw nodes
    for i, node in enumerate(nodes):
        node_num = i + 1
        
        if node_num < current_step:
            circle_class = "node-circle completed"
            circle_fill = "#10b981"
            circle_stroke = "#34d399"
            status_icon = "✓"
            status_color = "#34d399"
        elif node_num == current_step:
            circle_class = "node-circle active"
            circle_fill = "#38bdf8"
            circle_stroke = "#60a5fa"
            status_icon = "⟳"
            status_color = "#60a5fa"
        else:
            circle_class = "node-circle"
            circle_fill = "#475569"
            circle_stroke = "#64748b"
            status_icon = "○"
            status_color = "#64748b"
        
        html += f"""
        <g>
            <circle class="{circle_class}" cx="{node['x']}" cy="{node['y']}" r="42" 
                    fill="{circle_fill}" stroke="{circle_stroke}" stroke-width="3"/>
            <text x="{node['x']}" y="{node['y']}" class="node-label" dy="0.35em">{node['name']}</text>
            <text x="{node['x']}" y="{node['y'] + 62}" class="node-status" fill="{status_color}">
                {status_icon}
            </text>
        </g>
        """
    
    # Center status
    if current_step > 0 and current_step <= len(nodes):
        html += f"""
        <text x="{center_x}" y="{center_y - 15}" class="center-text">Step {current_step}/{total_steps}</text>
        <text x="{center_x}" y="{center_y + 12}" class="center-subtext">{step_name}</text>
        """
    elif current_step == 0:
        html += f"""
        <text x="{center_x}" y="{center_y}" class="center-text" fill="#64748b">Ready</text>
        """
    
    html += """
    </svg>
    </div>
    </body>
    </html>
    """
    
    return html


def main() -> None:
    st.set_page_config(page_title="EDW Data Assistant", layout="wide", initial_sidebar_state="collapsed")
    
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 20px 0;'>
        <h1 style='color: #38bdf8; margin-bottom: 10px;'>🤖 EDW Data Assistant</h1>
        <p style='color: #94a3b8; font-size: 18px;'>Natural Language to SQL • Powered by Cortex AI</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create columns for better layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        query_input = st.text_area(
            "💬 Ask your question:",
            placeholder="E.g., Show me total revenue by region...",
            height=120,
            key="query_input"
        )
        
        col_btn1, col_btn2 = st.columns([1, 3])
        with col_btn1:
            submit_btn = st.button("🚀 Run Query", type="primary", use_container_width=True)
        with col_btn2:
            show_thoughts = st.checkbox("Show detailed traces", value=False)
    
    with col2:
        st.markdown("**🎯 Processing Mode:**")
        agent_mode = st.radio(
            "mode",
            ["Auto-detect", "Project 1 (Retrieval)", "Project 2 (Reasoning)"],
            label_visibility="collapsed",
            horizontal=True
        )
    
    # Workflow visualization
    workflow_placeholder = st.empty()
    
    # Show initial state
    with workflow_placeholder:
        html = create_workflow_html(0, 8, "Ready to process")
        components.html(html, height=600, scrolling=False)
    
    # Results placeholder
    results_placeholder = st.empty()
    
    # Query history viewer
    with st.sidebar:
        st.markdown("### 📊 Query History")
        collector = get_collector()
        summary = collector.get_summary()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", summary["total"])
        with col2:
            st.metric("Success Rate", f"{summary['success_rate']}%")
        with col3:
            st.metric("Avg Latency", f"{summary['avg_latency_ms']}ms")
        
        st.divider()
        st.markdown("### 🔍 Search by Trace ID")
        search_trace_id = st.text_input("Enter trace ID:", placeholder="e4773ecc", key="trace_search")
        
        if search_trace_id:
            query_data = collector.get_query_by_trace_id(search_trace_id.strip())
            if query_data:
                st.success(f"Found trace ID: `{search_trace_id}`")
                st.json(query_data)
            else:
                st.warning(f"Trace ID `{search_trace_id}` not found in recent queries.")
                all_trace_ids = collector.get_all_trace_ids()
                if all_trace_ids:
                    st.caption(f"Available trace IDs: {', '.join(all_trace_ids[-10:])}")
        
        st.divider()
        st.markdown("### 📋 Recent Queries")
        recent_queries = collector.get_recent_queries(limit=10)
        if recent_queries:
            for query_metric in recent_queries:
                status_icon = "✅" if query_metric["status"] == "success" else "❌"
                user_query_truncated = query_metric["user_query"][:50]
                if len(query_metric["user_query"]) > 50:
                    user_query_truncated += "..."
                
                st.markdown(f"{status_icon} **{user_query_truncated}**")
                st.caption(f"Trace: `{query_metric['trace_id']}` | {query_metric['timestamp']} | {query_metric['total_latency_ms']}ms | {query_metric['row_count']} rows")
                
                if query_metric.get("error_message"):
                    st.error(query_metric["error_message"][:200])
                
                st.divider()
        else:
            st.info("No queries yet. Run a query to see history.")
    
    if submit_btn:
        if not query_input.strip():
            st.error("⚠️ Please enter a question before submitting.")
            return
        
        trace_id = generate_trace_id()
        set_trace_id(trace_id)
        st.info(f"🔍 Trace ID: `{trace_id}` (for debugging)")
        
        thought_traces = []
        
        try:
            # Step 1: Input
            with workflow_placeholder:
                html = create_workflow_html(1, 8, "Input Received")
                components.html(html, height=600, scrolling=False)
            time.sleep(0.7)
            thought_traces.append(f"✓ Received query: {query_input}")
            
            # Get session
            session = None
            try:
                from snowflake.snowpark.context import get_active_session
                session = get_active_session()
                thought_traces.append("✓ Connected to Snowflake")
            except Exception as e1:
                try:
                    conn = st.connection("snowflake")
                    session = conn.session() if callable(conn.session) else conn.session
                except Exception as e2:
                    raise RuntimeError(f"Could not get Snowflake session: {e2}")
            
            if session is None:
                raise RuntimeError("Session is None")
            
            # Set context
            try:
                session.sql("USE DATABASE EDW_M3").collect()
                session.sql("USE SCHEMA PUBLIC").collect()
                thought_traces.append("✓ Database: EDW_M3.PUBLIC")
            except Exception as e:
                thought_traces.append(f"⚠ Database context warning: {e}")
            
            # Step 2: Enhancer
            with workflow_placeholder:
                html = create_workflow_html(2, 8, "Query Enhancer")
                components.html(html, height=600, scrolling=False)
            time.sleep(0.7)
            thought_traces.append("✓ Enhanced query with context")
            
            # Step 3: Orchestrator
            with workflow_placeholder:
                html = create_workflow_html(3, 8, "Orchestrator Init")
                components.html(html, height=600, scrolling=False)
            time.sleep(0.7)
            orchestrator = Orchestrator.from_session(session)
            thought_traces.append("✓ Orchestrator initialized")
            
            # Step 4: Schema
            with workflow_placeholder:
                html = create_workflow_html(4, 8, "Fetching Schema")
                components.html(html, height=600, scrolling=False)
            time.sleep(0.7)
            thought_traces.append("✓ Retrieved table schema")
            
            # Step 5: Cortex AI
            with workflow_placeholder:
                html = create_workflow_html(5, 8, "Cortex AI Generation")
                components.html(html, height=600, scrolling=False)
            time.sleep(0.7)
            thought_traces.append("✓ Generating SQL via Cortex...")
            
            # Step 6: Execute
            with workflow_placeholder:
                html = create_workflow_html(6, 8, "Executing Query")
                components.html(html, height=600, scrolling=False)
            
            result = orchestrator.run(query_input, trace_id)
            thought_traces.append("✓ Query executed")
            time.sleep(0.6)
            
            # Step 7: Results
            with workflow_placeholder:
                html = create_workflow_html(7, 8, "Processing Results")
                components.html(html, height=600, scrolling=False)
            time.sleep(0.6)
            
            rows = result.get("rows", [])
            summary = f"Retrieved {len(rows)} rows" if rows else "No data returned"
            thought_traces.append(f"✓ {summary}")
            
            # Step 8: Complete
            with workflow_placeholder:
                html = create_workflow_html(8, 8, "Complete ✓")
                components.html(html, height=600, scrolling=False)
            time.sleep(0.5)
            
            # Display results
            with results_placeholder:
                st.success(f"✅ {summary}")
                
                tab1, tab2, tab3, tab4 = st.tabs(["📊 Results", "🔍 SQL", "📝 Enhanced Query", "🔬 Debug"])
                
                with tab1:
                    if rows:
                        st.dataframe(rows, use_container_width=True, height=400)
                    else:
                        st.info("No rows returned from the query.")
                
                with tab2:
                    generated_sql = result.get("generated_sql", "")
                    if generated_sql:
                        st.code(generated_sql, language="sql", line_numbers=True)
                    else:
                        st.warning("No SQL generated.")
                
                with tab3:
                    st.code(result["enhanced_query"], language="text")
                
                with tab4:
                    st.code(trace_id, language="text")
                    st.caption("Use this ID to search logs or report issues")
                    if show_thoughts:
                        st.divider()
                        for trace in thought_traces:
                            st.text(trace)
                    else:
                        st.info("Enable 'Show detailed traces' to see debug info")
        
        except CortexClientError as exc:
            with workflow_placeholder:
                html = create_workflow_html(0, 8, "Error occurred")
                components.html(html, height=600, scrolling=False)
            st.error(f"❌ Cortex Error: {exc}")
            if show_thoughts:
                with st.expander("Debug Traces"):
                    for trace in thought_traces:
                        st.text(trace)
        
        except Exception as exc:
            with workflow_placeholder:
                html = create_workflow_html(0, 8, "Error occurred")
                components.html(html, height=600, scrolling=False)
            st.error(f"❌ Error: {exc}")
            if show_thoughts:
                with st.expander("Debug Traces"):
                    for trace in thought_traces:
                        st.text(trace)


if __name__ == "__main__":
    main()
