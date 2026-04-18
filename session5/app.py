"""
Robotic Chef Platform - Multi-Agent AI System (Budget Extension)
================================================================
Session 5: The Challenge - Agent-to-Agent (A2A) Integration

Extended with a Smart Budget mode that:
  - Adds a budget slider (£5–£50)
  - Adds a people count input (1–8)
  - Adds dietary filter chips (none / vegetarian / vegan / gluten-free / pescatarian)
  - Calls run_budget_chef_pipeline() which uses the new MCP tools:
      fit_budget, get_nutrition, get_price

The original Dish Mode (type a dish name) is preserved as a tab so
existing behaviour is unchanged.

Run with:
    streamlit run app.py
"""

import streamlit as st
import asyncio
import os
from dotenv import load_dotenv

from agents import run_robotic_chef_pipeline, run_budget_chef_pipeline
import llm_client

load_dotenv()

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Robotic Chef Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("How It Works")
    st.markdown(
        """
        Two specialised AI agents communicate via **Agent-to-Agent (A2A)** messaging:

        **Agent 1 — Food Analysis**
        - Connects to the Recipe MCP Server
        - *Budget mode:* calls `fit_budget`, `get_nutrition`, `get_price`
          to pick the best dish within your budget
        - *Dish mode:* analyses the dish you specify
        - Produces a structured task specification

        **Agent 2 — Robotics Designer**
        - Receives the task spec from Agent 1
        - Connects to the Robotics MCP Server
        - Searches component, sensor and actuator databases
        - Designs a complete robotic cooking platform

        The output of Agent 1 flows directly into Agent 2 — this is the A2A
        pattern in action.
        """
    )

    st.divider()
    st.header("New MCP Tools (Budget Mode)")
    st.markdown(
        """
        Three new tools were added to `recipe_mcp_server.py`:

        | Tool | What it does |
        |------|-------------|
        | `fit_budget(budget, people, filter)` | Ranked list of dishes within budget |
        | `get_nutrition(dish, servings)` | Protein, carbs, fat, kcal, vitamins |
        | `get_price(dish, servings)` | Cost, cost/person, protein-per-£1 score |
        """
    )

    st.divider()
    st.header("Example Dishes (Dish Mode)")
    st.markdown(
        """
        Pasta Carbonara · Cheese Soufflé · Sushi Rolls
        Pizza Margherita · Beef Stir-Fry · Chocolate Cake
        Fish and Chips · Pad Thai · French Omelette · Artisan Bread
        """
    )

    st.divider()
    st.caption("AI Workshop — Session 5: The Challenge\nUniversity of Hertfordshire")

# ---------------------------------------------------------------------------
# LLM token check
# ---------------------------------------------------------------------------

llm_token = os.getenv("LLM_API_TOKEN", "")
if not llm_token or llm_token == "your-token-here":
    st.warning(
        "**LLM API token not configured.** "
        "Create a `.env` file in the session5 directory:\n\n"
        "```\nLLM_SERVICE_URL=http://localhost:8000\nLLM_API_TOKEN=your-token\n```"
    )

# ---------------------------------------------------------------------------
# Main title
# ---------------------------------------------------------------------------

st.title("Robotic Chef Platform")
st.markdown("### Agent-to-Agent Multi-Agent System")

# ---------------------------------------------------------------------------
# Mode tabs
# ---------------------------------------------------------------------------

tab_budget, tab_dish = st.tabs(["💰 Smart Budget Mode", "🍽️ Dish Mode"])

# ============================================================
# TAB 1: Budget Mode
# ============================================================
with tab_budget:
    st.markdown(
        "Agent 1 will use `fit_budget`, `get_nutrition`, and `get_price` to find "
        "the best dish within your budget, then pass a full task specification to "
        "Agent 2 to design the robot."
    )

    col_left, col_right = st.columns(2, gap="large")

    with col_left:
        st.subheader("Budget & People")

        budget = st.slider(
            "Total budget (£)",
            min_value=5,
            max_value=50,
            value=15,
            step=1,
            format="£%d",
            help="Ingredient cost for the whole meal",
        )

        people = st.number_input(
            "Number of people",
            min_value=1,
            max_value=8,
            value=2,
            step=1,
        )

        st.caption(f"Budget per person: £{budget / people:.2f}")

    with col_right:
        st.subheader("Dietary Requirements")

        dietary_options = {
            "None (no restriction)": "none",
            "Vegetarian": "vegetarian",
            "Vegan": "vegan",
            "Gluten-free": "gluten_free",
            "Pescatarian": "pescatarian",
        }
        diet_label = st.radio(
            "Filter",
            options=list(dietary_options.keys()),
            index=0,
            label_visibility="collapsed",
        )
        dietary_filter = dietary_options[diet_label]

    st.divider()
    run_budget_btn = st.button(
        f"Design Budget Robot Chef — £{budget} for {people} people",
        type="primary",
        use_container_width=True,
        key="run_budget",
    )

    if run_budget_btn:
        status_container = st.status(
            f"Finding best dish for £{budget} / {people} people ({diet_label})…",
            expanded=True,
        )
        status_lines = []

        def budget_status_callback(msg: str):
            status_lines.append(msg)
            with status_container:
                st.text(msg)

        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(
                        asyncio.run,
                        run_budget_chef_pipeline(
                            budget_gbp=float(budget),
                            people=int(people),
                            dietary_filter=dietary_filter,
                            status_callback=budget_status_callback,
                        ),
                    ).result()
            else:
                result = asyncio.run(
                    run_budget_chef_pipeline(
                        budget_gbp=float(budget),
                        people=int(people),
                        dietary_filter=dietary_filter,
                        status_callback=budget_status_callback,
                    )
                )

            status_container.update(label="Pipeline complete!", state="complete", expanded=False)

            st.divider()

            # Summary banner
            st.success(
                f"Budget: **£{result['budget_gbp']:.2f}** · "
                f"People: **{result['people']}** · "
                f"Diet: **{result['dietary_filter']}**"
            )

            with st.expander("Agent 1: Budget Food Analysis & Dish Selection", expanded=False):
                st.markdown(result["food_analysis"])

            with st.expander("Agent 2: Robot Design", expanded=True):
                st.markdown(result["robot_design"])

        except Exception as e:
            status_container.update(label="Pipeline failed", state="error")
            st.error(f"An error occurred: {e}")
            st.exception(e)

# ============================================================
# TAB 2: Dish Mode (original, unchanged)
# ============================================================
with tab_dish:
    st.markdown(
        "Enter a dish name and both agents will run as before — Agent 1 analyses the "
        "dish, Agent 2 designs the robot."
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        dish_name = st.text_input(
            "Dish name",
            placeholder="e.g. pasta carbonara, sushi rolls, chocolate cake…",
            label_visibility="collapsed",
            key="dish_input",
        )
    with col2:
        run_dish_btn = st.button(
            "Design Robot Chef",
            type="primary",
            use_container_width=True,
            key="run_dish",
        )

    if run_dish_btn and dish_name:
        status_container = st.status(
            f"Designing a robot chef for: **{dish_name}**", expanded=True
        )
        status_lines = []

        def dish_status_callback(msg: str):
            status_lines.append(msg)
            with status_container:
                st.text(msg)

        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(
                        asyncio.run,
                        run_robotic_chef_pipeline(dish_name, dish_status_callback),
                    ).result()
            else:
                result = asyncio.run(run_robotic_chef_pipeline(dish_name, dish_status_callback))

            status_container.update(label="Pipeline complete!", state="complete", expanded=False)

            st.divider()
            with st.expander("Agent 1: Food Analysis", expanded=False):
                st.markdown(result["food_analysis"])
            with st.expander("Agent 2: Robot Design", expanded=True):
                st.markdown(result["robot_design"])

        except Exception as e:
            status_container.update(label="Pipeline failed", state="error")
            st.error(f"An error occurred: {e}")
            st.exception(e)

    elif run_dish_btn and not dish_name:
        st.warning("Please enter a dish name to get started.")
