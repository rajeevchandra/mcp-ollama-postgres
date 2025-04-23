import streamlit as st
import requests
import os
import pandas as pd
import altair as alt
import json
import re  # ✅ Add this!


API_URL = os.getenv("MCP_API_URL", "http://mcp-server:3333/mcp")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")

st.title("📊 MCP Streamlit Dashboard")

# List tables
try:
    resp = requests.get(f"{API_URL}/table%3A%2F%2Flist")
    tables = resp.json()
    st.write("Available Tables:", tables)
except Exception as e:
    st.error(f"Failed to connect to MCP API: {e}")
    st.stop()

table_name = st.selectbox("Choose a table", tables)

df = None

# Manual SQL
if st.button("Query selected table"):
    query = f"SELECT * FROM {table_name} LIMIT 100"
    response = requests.post(f"{API_URL}/sql%3A%2F%2Fquery", json={"query": query})
    if response.ok:
        rows = response.json()
        df = pd.DataFrame(rows)
        st.dataframe(df)

        if not df.empty:
            st.download_button("📥 Export as CSV", df.to_csv(index=False), "query_results.csv", "text/csv")

            st.subheader("📈 Chart Preview")
            numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
            date_cols = df.select_dtypes(include=["datetime64", "object"]).columns
            date_cols = date_cols[date_cols.to_series().str.contains("date|time", case=False, regex=True)]

            if len(numeric_cols) >= 1:
                x_axis = st.selectbox("X-axis", df.columns)
                y_axis = st.selectbox("Y-axis", numeric_cols)
                chart = alt.Chart(df).mark_bar().encode(
                    x=x_axis,
                    y=y_axis
                ).properties(height=400)
                st.altair_chart(chart, use_container_width=True)

            if len(date_cols) > 0 and len(numeric_cols) > 0:
                st.subheader("⏱️ Time Series Chart")
                date_field = st.selectbox("Time Column", date_cols)
                value_field = st.selectbox("Value Column", numeric_cols)
                df[date_field] = pd.to_datetime(df[date_field], errors="coerce")
                ts_chart = alt.Chart(df.dropna()).mark_line().encode(
                    x=date_field,
                    y=value_field
                ).properties(height=400)
                st.altair_chart(ts_chart, use_container_width=True)

            st.subheader("📊 Statistical Summary")
            st.dataframe(df.describe())

            if len(numeric_cols) > 1:
                st.subheader("📉 Correlation Matrix")
                st.dataframe(df[numeric_cols].corr())
    else:
        st.error(f"Query failed: {response.text}")

# Prompt-based SQL via Ollama
st.markdown("---")
st.subheader("💡 Ask a data question (Ollama-powered)")

prompt = st.text_input("e.g. Show average salary by department, or employees in NY earning > 80000")

if st.button("Generate SQL from Prompt"):
    system_prompt = f"You are a helpful data analyst. Generate a valid PostgreSQL SQL query to answer the question using the table '{table_name}'. Return only SQL. Don't explain."
    payload = {
        "model": "qwen2.5:latest",
        "prompt": f"{system_prompt}\\n\\nUser: {prompt}",
        "stream": False
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload)

        st.subheader("🔍 Raw Ollama Response")
        st.code(r.text)  # <-- this will show exactly what Ollama returned

        try:
            # Use regex to extract the first valid JSON object from Ollama response
            match = re.search(r'\{.*?\}', r.text, re.DOTALL)
            if not match:
                raise ValueError("No valid JSON object found in response")

            raw_json = json.loads(match.group(0))
            generated_sql = raw_json.get("response", "").strip("```sql").strip("```").strip()

        except Exception as e:
            st.error(f"❌ Failed to parse Ollama response: {e}")
            st.text("🔍 Raw Ollama response:")
            st.code(r.text)
            st.stop()

        st.code(generated_sql, language="sql")

        response = requests.post(f"{API_URL}/sql%3A%2F%2Fquery", json={"query": generated_sql})
        if response.ok:
            result = pd.DataFrame(response.json())
            st.dataframe(result)
            st.download_button("📥 Export Prompt Result", result.to_csv(index=False), "prompt_result.csv", "text/csv")
            if not result.empty:
                if "date" in result.columns[0].lower() or "time" in result.columns[0].lower():
                    result[result.columns[0]] = pd.to_datetime(result[result.columns[0]], errors="coerce")
                st.bar_chart(result.set_index(result.columns[0]))
        else:
            st.error(f"Query failed: {response.text}")
    except Exception as e:
        st.error(f"Ollama error: {e}")