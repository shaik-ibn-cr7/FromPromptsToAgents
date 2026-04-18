"""
Multi-Agent System: Recipe Agent + Robotics Agent with A2A Communication.
=========================================================================
Session 5: The Challenge - Robotic Chef Platform (Budget Extension)

Extended from the Session 4 baseline with:
  - run_budget_chef_pipeline(): budget-aware A2A pipeline
  - BUDGET_FOOD_ANALYSIS_SYSTEM_PROMPT: instructs Agent 1 to use the new
    get_nutrition / get_price / fit_budget MCP tools before picking a dish
  - run_budget_food_analysis_agent(): budget-aware Agent 1

The original run_robotic_chef_pipeline() and all its helpers are unchanged
so the existing Streamlit UI keeps working without modification.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import llm_client

SERVER_DIR = Path(__file__).parent


# ---------------------------------------------------------------------------
# Core: Run an agent loop with an MCP server  (unchanged)
# ---------------------------------------------------------------------------

async def run_agent_with_mcp(
    server_script: str,
    system_prompt: str,
    user_message: str,
    status_callback=None,
) -> str:
    """
    Generic function to run an LLM agent loop connected to an MCP server.

    The agent will:
    1. Connect to the specified MCP server via stdio
    2. Discover available tools and convert them to a simple format
    3. Send the user message to the LLM with the tool definitions
    4. Execute any tool calls the LLM requests via the MCP session
    5. Feed tool results back to the LLM
    6. Repeat until the LLM produces a final text response (max 10 iterations)

    Args:
        server_script: Absolute or relative path to the MCP server Python file.
        system_prompt: The system prompt defining the agent's role and behaviour.
        user_message: The user's input message to the agent.
        status_callback: Optional callable(str) for real-time status updates.

    Returns:
        The agent's final text response.
    """

    def _status(msg: str):
        if status_callback:
            status_callback(msg)

    _status(f"Starting MCP server: {Path(server_script).name}")
    server_path = str(Path(server_script).resolve())
    server_params = StdioServerParameters(command=sys.executable, args=[server_path])

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            _status("MCP session initialised")

            tools_result = await session.list_tools()
            tools = [
                {
                    "name": t.name,
                    "description": t.description or "",
                    "parameters": t.inputSchema if t.inputSchema else {"type": "object", "properties": {}},
                }
                for t in tools_result.tools
            ]
            _status(f"Discovered {len(tools)} tools: {', '.join(t['name'] for t in tools)}")

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]

            last_content = ""
            for iteration in range(10):
                _status(f"LLM call (iteration {iteration + 1})")
                response = llm_client.chat(messages, tools=tools)

                if response["tool_calls"]:
                    messages.append({"role": "assistant", "content": response["raw"]})
                    for tc in response["tool_calls"]:
                        fn_name = tc["name"]
                        fn_args = tc["arguments"]
                        _status(f"Calling tool: {fn_name}")
                        try:
                            result = await session.call_tool(fn_name, fn_args)
                            tool_output = ""
                            if result.content:
                                for content_block in result.content:
                                    if hasattr(content_block, "text"):
                                        tool_output += content_block.text
                            _status(f"Tool {fn_name} returned {len(tool_output)} chars")
                        except Exception as e:
                            tool_output = json.dumps({"error": str(e)})
                            _status(f"Tool {fn_name} error: {e}")
                        messages.append({"role": "tool", "name": fn_name, "content": tool_output})
                else:
                    _status("Agent produced final response")
                    return response["content"] or ""

                last_content = response.get("content") or ""

            _status("Max iterations reached")
            return last_content or "Agent did not produce a final response within the iteration limit."


# ---------------------------------------------------------------------------
# Agent 1 (original): Food Analysis Agent  (unchanged)
# ---------------------------------------------------------------------------

FOOD_ANALYSIS_SYSTEM_PROMPT = """\
You are the Food Analysis Agent, an expert culinary analyst. Your role is to \
thoroughly analyse a dish and produce a detailed, structured task specification \
that a Robotics Design Agent can use to design an automated cooking robot.

When given a dish name, use the available tools to:
1. Analyse the dish fully (ingredients, steps, techniques)
2. Get the detailed cooking techniques
3. Get equipment specifications for key equipment
4. Get safety requirements

Then synthesise all this information into a comprehensive TASK SPECIFICATION \
with the following clearly labelled sections:

## Dish Overview
- Name, cuisine, difficulty, servings, total time

## Physical Tasks Required
For each step, describe the physical action needed:
- Cutting/chopping (specify precision, force, dimensions)
- Stirring/mixing (specify speed, duration, force)
- Pouring/dispensing (specify volume, precision, temperature)
- Heating/temperature control (specify temperatures, durations, precision)
- Timing coordination (specify concurrent operations)

## Cooking Techniques with Precision Requirements
List each technique with:
- Temperature requirements (exact values in C)
- Duration requirements
- Precision level (critical/high/medium)
- Failure modes if done incorrectly

## Equipment to Operate
For each piece of equipment:
- What it is and how it must be operated
- Temperature ranges
- Physical interaction needed (knobs, handles, placement)

## Safety Requirements
- Temperature hazards and maximum temperatures
- Splash/splatter risks
- Timing-critical steps
- Food safety considerations

## Robotics Task Specification
A summary designed specifically for a Robotics Design Agent, listing:
- All manipulation tasks (with required degrees of freedom and force ranges)
- All sensing requirements (temperature, vision, force feedback)
- Workspace requirements (dimensions, stations)
- Speed and timing constraints
- Safety constraints for the robot

Be thorough and specific - the Robotics Agent depends entirely on your analysis \
to design an appropriate robot. Include exact temperatures, durations, and force \
estimates wherever possible.
"""


async def run_food_analysis_agent(dish_name: str, status_callback=None) -> str:
    """Run Agent 1: Food Analysis Agent (original, dish-name-driven)."""
    server_script = str(SERVER_DIR / "recipe_mcp_server.py")
    user_message = (
        f"Please analyse the dish '{dish_name}' in complete detail. "
        f"Use all available tools to gather comprehensive information, then produce "
        f"a full task specification for the Robotics Design Agent."
    )
    return await run_agent_with_mcp(
        server_script=server_script,
        system_prompt=FOOD_ANALYSIS_SYSTEM_PROMPT,
        user_message=user_message,
        status_callback=status_callback,
    )


# ---------------------------------------------------------------------------
# Agent 1 (NEW): Budget-Aware Food Analysis Agent
# ---------------------------------------------------------------------------

BUDGET_FOOD_ANALYSIS_SYSTEM_PROMPT = """\
You are the Smart Budget Food Analysis Agent, an expert culinary analyst and \
nutritionist. Your role is to:

1. Use fit_budget() to find all dishes within the user's budget and people count, \
   applying any dietary filter requested.
2. Use get_nutrition() and get_price() on the top candidates to compare them in detail.
3. CHOOSE the single best dish by balancing:
   - Cost vs nutrition (protein and key vitamins)
   - Dietary requirements
   - Cooking feasibility
4. Use analyse_dish(), get_cooking_techniques(), and get_safety_requirements() to \
   fully analyse the chosen dish.
5. Produce a BUDGET TASK SPECIFICATION with these clearly labelled sections:

## Budget Summary
- Budget, people, dietary filter
- All dishes considered (name, cost, protein)
- Chosen dish and WHY (explicit trade-off reasoning)

## Dish Overview
- Name, cuisine, difficulty, servings, total time

## Nutritional Profile (for chosen dish, scaled to requested people)
- Protein, carbs, fat, fibre, kcal per person and total
- Key vitamins provided
- Allergens

## Cost Breakdown
- Total cost, cost per person, budget remaining
- Value score (protein per £1)

## Physical Tasks Required
For each cooking step, describe the physical action:
- Cutting/chopping (precision, force, dimensions)
- Stirring/mixing (speed, duration)
- Pouring/dispensing (volume, temperature)
- Heating/temperature control (exact temperatures, durations)
- Timing coordination

## Cooking Techniques with Precision Requirements
Each technique with temperature, duration, precision level, failure modes.

## Equipment to Operate
Each piece of equipment with operating requirements and physical interactions.

## Safety Requirements
Temperature hazards, splash risks, timing-critical steps, food safety.

## Robotics Task Specification
A summary for the Robotics Design Agent:
- All manipulation tasks with DoF and force ranges
- Sensing requirements (temperature, vision, weight, force)
- Workspace requirements
- Speed and timing constraints
- Safety constraints

Be thorough. The Robotics Agent depends entirely on your analysis.
"""


async def run_budget_food_analysis_agent(
    budget_gbp: float,
    people: int,
    dietary_filter: str = "none",
    status_callback=None,
) -> str:
    """
    Run the budget-aware Agent 1.

    Uses fit_budget, get_nutrition, and get_price to pick the best dish
    within budget before doing the full task-specification analysis.

    Args:
        budget_gbp:      Total budget in GBP.
        people:          Number of people to feed.
        dietary_filter:  'none' | 'vegetarian' | 'vegan' | 'gluten_free' | 'pescatarian'
        status_callback: Optional callable(str) for real-time status updates.

    Returns:
        A detailed budget task specification string.
    """
    server_script = str(SERVER_DIR / "recipe_mcp_server.py")
    user_message = (
        f"I have a budget of £{budget_gbp:.2f} for {people} people. "
        f"Dietary requirement: {dietary_filter}. "
        f"Please use fit_budget to find all dishes within this budget, "
        f"compare their nutrition and cost using get_nutrition and get_price, "
        f"then choose the best dish. Fully analyse the chosen dish using "
        f"analyse_dish, get_cooking_techniques, and get_safety_requirements. "
        f"Produce a complete budget task specification for the Robotics Design Agent."
    )
    return await run_agent_with_mcp(
        server_script=server_script,
        system_prompt=BUDGET_FOOD_ANALYSIS_SYSTEM_PROMPT,
        user_message=user_message,
        status_callback=status_callback,
    )


# ---------------------------------------------------------------------------
# Agent 2: Robotics Designer Agent  (unchanged)
# ---------------------------------------------------------------------------

ROBOTICS_DESIGN_SYSTEM_PROMPT = """\
You are the Robotics Design Agent, an expert in designing robotic systems for \
food preparation and cooking tasks. You receive a detailed task specification \
from the Food Analysis Agent and must design a complete robotic cooking platform.

Use the available tools to:
1. Search for suitable robot arms/platforms based on the task requirements
2. Find appropriate sensors for the required sensing capabilities
3. Find actuators and end-effectors for the required manipulation tasks
4. Get detailed specifications for each selected component
5. Use the recommendation tool for an initial platform suggestion

Then design a complete robotic system with these clearly labelled sections:

## Robot Design Overview
- Robot type and form factor rationale
- Single-arm vs dual-arm justification
- Stationary vs mobile justification

## Selected Components
For each component, provide:
- Component ID and name
- Key specifications
- Why it was chosen for this specific dish

## Sensor Suite
For each sensor:
- Sensor ID and name
- What it monitors and why
- Mounting location recommendation

## Actuators and End-Effectors
For each actuator:
- Actuator ID and name
- What task it performs
- Key specifications relevant to the cooking task

## Motion and Control Requirements
- Degrees of freedom needed and why
- Speed requirements for time-critical operations
- Force control requirements
- Coordination between multiple operations

## Safety and Compliance
- How the robot handles high-temperature operations safely
- Human-robot interaction safety measures
- Food safety compliance
- Emergency stop scenarios

## Platform Summary Table
A clear summary table with all selected components, their IDs, and roles.

## Estimated Capabilities
- Which steps the robot can perform fully autonomously
- Which steps may need human oversight
- Overall autonomy percentage estimate

Be specific and reference actual component IDs from the database. Justify every \
selection based on the task specification you received.
"""


async def run_robotics_agent(task_specification: str, status_callback=None) -> str:
    """Run Agent 2: Robotics Designer Agent."""
    server_script = str(SERVER_DIR / "robotics_mcp_server.py")
    user_message = (
        f"Based on the following task specification from the Food Analysis Agent, "
        f"design a complete robotic cooking platform. Search the component databases "
        f"thoroughly and select the best components for each requirement.\n\n"
        f"--- TASK SPECIFICATION ---\n{task_specification}\n--- END SPECIFICATION ---"
    )
    return await run_agent_with_mcp(
        server_script=server_script,
        system_prompt=ROBOTICS_DESIGN_SYSTEM_PROMPT,
        user_message=user_message,
        status_callback=status_callback,
    )


# ---------------------------------------------------------------------------
# Pipeline A: Original Robotic Chef Pipeline (unchanged)
# ---------------------------------------------------------------------------

async def run_robotic_chef_pipeline(dish_name: str, status_callback=None) -> dict:
    """
    Run the full Robotic Chef A2A pipeline (original, dish-name-driven).

    Returns:
        dict with keys 'food_analysis' and 'robot_design'.
    """
    def _status(msg: str):
        if status_callback:
            status_callback(msg)

    _status("=== Stage 1: Food Analysis Agent ===")
    food_analysis = await run_food_analysis_agent(dish_name=dish_name, status_callback=status_callback)
    _status("Food Analysis Agent complete")

    _status("=== Stage 2: Robotics Designer Agent ===")
    robot_design = await run_robotics_agent(task_specification=food_analysis, status_callback=status_callback)
    _status("Robotics Designer Agent complete")

    return {"food_analysis": food_analysis, "robot_design": robot_design}


# ---------------------------------------------------------------------------
# Pipeline B (NEW): Budget-Aware Robotic Chef Pipeline
# ---------------------------------------------------------------------------

async def run_budget_chef_pipeline(
    budget_gbp: float,
    people: int,
    dietary_filter: str = "none",
    status_callback=None,
) -> dict:
    """
    Run the budget-aware Robotic Chef A2A pipeline.

    Stage 1: Budget Food Analysis Agent picks the best dish within budget,
             checks nutrition/cost, and produces a full task specification.
    Stage 2: Robotics Designer Agent designs a robot for the chosen dish.

    Args:
        budget_gbp:      Total budget in GBP.
        people:          Number of people to feed.
        dietary_filter:  Dietary restriction string.
        status_callback: Optional callable(str) for real-time status updates.

    Returns:
        dict with keys:
            'food_analysis'  — Budget Task Specification from Agent 1
            'robot_design'   — Robot Design from Agent 2
            'budget_gbp'     — echo of budget
            'people'         — echo of people
            'dietary_filter' — echo of filter
    """
    def _status(msg: str):
        if status_callback:
            status_callback(msg)

    _status("=== Stage 1: Budget Food Analysis Agent ===")
    food_analysis = await run_budget_food_analysis_agent(
        budget_gbp=budget_gbp,
        people=people,
        dietary_filter=dietary_filter,
        status_callback=status_callback,
    )
    _status("Budget Food Analysis Agent complete")

    _status("=== Stage 2: Robotics Designer Agent ===")
    robot_design = await run_robotics_agent(
        task_specification=food_analysis,
        status_callback=status_callback,
    )
    _status("Robotics Designer Agent complete")

    return {
        "food_analysis": food_analysis,
        "robot_design": robot_design,
        "budget_gbp": budget_gbp,
        "people": people,
        "dietary_filter": dietary_filter,
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

async def _main():
    import argparse

    parser = argparse.ArgumentParser(description="Robotic Chef Pipeline - CLI")
    subparsers = parser.add_subparsers(dest="mode")

    # Original mode
    dish_parser = subparsers.add_parser("dish", help="Analyse a specific dish")
    dish_parser.add_argument("name", nargs="?", default="pasta carbonara")

    # Budget mode
    budget_parser = subparsers.add_parser("budget", help="Pick best dish within budget")
    budget_parser.add_argument("--budget", type=float, default=15.0)
    budget_parser.add_argument("--people", type=int, default=2)
    budget_parser.add_argument("--diet", default="none")

    args = parser.parse_args()

    def print_status(msg: str):
        print(f"  [{msg}]")

    if args.mode == "budget" or (hasattr(args, "budget") and args.mode is None):
        print(f"\nBudget Chef Pipeline — £{args.budget:.2f} for {args.people} people ({args.diet})")
        print("=" * 60)
        result = await run_budget_chef_pipeline(
            budget_gbp=args.budget,
            people=args.people,
            dietary_filter=args.diet,
            status_callback=print_status,
        )
    else:
        dish = getattr(args, "name", "pasta carbonara")
        print(f"\nRobotic Chef Pipeline — Analysing: {dish}")
        print("=" * 60)
        result = await run_robotic_chef_pipeline(dish_name=dish, status_callback=print_status)

    print("\n" + "=" * 60)
    print("FOOD ANALYSIS (Agent 1)")
    print("=" * 60)
    print(result["food_analysis"])
    print("\n" + "=" * 60)
    print("ROBOT DESIGN (Agent 2)")
    print("=" * 60)
    print(result["robot_design"])


if __name__ == "__main__":
    asyncio.run(_main())
