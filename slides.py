"""
AI-module (template-based) to generate explanatory slides + narration script
from a retrieved concept (from knowledge_graph.json).

What it does:
- Loads a concept and its text (definition + related topics) from knowledge_graph.json
- Generates a small slide deck (structured JSON) using human-readable templates
- Generates a narration script for the slides
- Optionally writes a tiny Manim python file that visualizes the first slide

Design choices / Thought process:
- We use deterministic templates (no LLM) to keep output predictable and fast.
- We produce structured JSON so downstream modules (formatter -> Manim) can consume it.
- Slide types are small and pedagogically sensible: Title, Definition, Example, Related.
- We provide 'audience_level' to vary wording slightly (beginner/advanced).
- This is intentionally small-scale and explainable for demo purposes.
"""

import json
import os
from datetime import datetime

# ---------------------------
# Config / Templates
# ---------------------------

# How many bullets on content slides
BULLETS_PER_SLIDE = 3

# Simple templates for narration
TITLE_INTRO_TEMPLATE = "Welcome — today we'll learn about {concept}."
DEFINITION_TEMPLATE_BEGINNER = (
    "{concept} can be understood as: {definition} "
    "I'll explain the idea step by step with a simple example."
)
DEFINITION_TEMPLATE_ADVANCED = (
    "Formally, {concept} is: {definition} "
    "We'll also highlight important properties and implications."
)
EXAMPLE_TEMPLATE = (
    "Example: Consider {example_brief}. This demonstrates the main idea: {example_point}."
)
RELATED_TEMPLATE = "Related topics you might want to learn next: {related_list}."

# ---------------------------
# Utilities
# ---------------------------
def safe_join(lst):
    """Join a list of strings, handling empty or missing values gracefully."""
    return ", ".join([str(x) for x in lst if x])

def truncate_text(text, max_words=30):
    """Short helper to make short example headlines (not strict, just for demo)."""
    words = text.split()
    return " ".join(words[:max_words]) + ("..." if len(words) > max_words else "")

# ---------------------------
# Core generator functions
# ---------------------------
def generate_slide_deck(concept_name, definition, related, audience_level="beginner"):
    """
    Given a concept name, definition (string), and related topics (list),
    produce a list of slide dicts and a narration script.
    """
    # Thought: keep a small, pedagogical structure that is easy to present in 1-3 minutes.
    slides = []
    narration_lines = []

    # Slide 0: Title slide
    title_slide = {
        "type": "title",
        "title": f"Introduction to {concept_name}",
        "subtitle": truncate_text(definition, max_words=15),
        "duration_sec": 4
    }
    slides.append(title_slide)
    narration_lines.append(TITLE_INTRO_TEMPLATE.format(concept=concept_name))

    # Slide 1: Definition slide
    def_template = DEFINITION_TEMPLATE_BEGINNER if audience_level == "beginner" else DEFINITION_TEMPLATE_ADVANCED
    definition_text = def_template.format(concept=concept_name, definition=definition)
    definition_slide = {
        "type": "definition",
        "title": f"What is {concept_name}?",
        "bullets": [
            # Break the definition into 1-3 digestible bullets for a slide.
            truncate_text(definition, max_words=20)
        ],
        "notes": definition_text,
        "duration_sec": 10
    }
    slides.append(definition_slide)
    narration_lines.append(definition_text)

    # Slide 2: Simple example slide
    # Thought: If KG doesn't contain an example, make a tiny illustrative example using related topic
    example_brief = None
    example_point = None
    if related:
        # pick the first related topic as basis for a tiny example
        example_brief = f"a simple case involving {related[0]}"
        example_point = f"how {concept_name} uses {related[0]} in structure/operation"
    else:
        example_brief = f"a simple conceptual scenario"
        example_point = f"the core intuition behind {concept_name}"

    example_slide = {
        "type": "example",
        "title": f"Simple example: {truncate_text(example_brief, max_words=6)}",
        "bullets": [
            "Set up the scenario",
            f"Apply the core idea of {concept_name}",
            "Observe the result / takeaway"
        ],
        "notes": EXAMPLE_TEMPLATE.format(example_brief=example_brief, example_point=example_point),
        "duration_sec": 12
    }
    slides.append(example_slide)
    narration_lines.append(example_slide["notes"])

    # Slide 3: Related concepts / next steps
    related_list_str = safe_join(related) if related else "No related topics available."
    related_slide = {
        "type": "related",
        "title": "Related topics & next steps",
        "bullets": related if related else ["Further reading not available"],
        "notes": RELATED_TEMPLATE.format(related_list=related_list_str),
        "duration_sec": 6
    }
    slides.append(related_slide)
    narration_lines.append(related_slide["notes"])

    # Final: short summary
    summary = f"In summary, {concept_name}: {truncate_text(definition, max_words=20)}"
    slides.append({
        "type": "summary",
        "title": "Summary",
        "bullets": [truncate_text(definition, max_words=20)],
        "notes": summary,
        "duration_sec": 6
    })
    narration_lines.append(summary)

    # Put together the full narration script
    full_script = "\n\n".join(narration_lines)

    # Deck metadata
    deck = {
        "concept": concept_name,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "audience_level": audience_level,
        "slides": slides
    }

    return deck, full_script

# ---------------------------
# Optional: write a minimal Manim scene file
# ---------------------------
def write_simple_manim(deck, out_path="generated_manim.py"):
    """
    Create a tiny Manim script that visualizes the first slide as a title + subtitle.
    This is intentionally minimal — suitable for Manim Community edition.
    """
    # Thought: keep the generated Manim code small so students can run it quickly.
    first_slide = deck["slides"][0] if deck["slides"] else None
    if not first_slide:
        return None

    title = first_slide.get("title", "Title")
    subtitle = first_slide.get("subtitle", "")

    manim_code = f"""\
# Auto-generated Manim scene (Community Manim)
# To render: manim -pql {os.path.basename(out_path)} SimpleTitleScene
from manim import *

class SimpleTitleScene(Scene):
    def construct(self):
        title = Text({json.dumps(title)}).scale(1.2).to_edge(UP)
        subtitle = Text({json.dumps(subtitle)}).scale(0.6).next_to(title, DOWN)
        self.play(Write(title))
        self.wait(0.6)
        self.play(Write(subtitle))
        self.wait(2)
"""

    with open(out_path, "w") as f:
        f.write(manim_code)
    return out_path

# ---------------------------
# Main: load KG -> generate deck -> save outputs
# ---------------------------
def main(concept_query, audience_level="beginner"):
    # 1) load the simple knowledge graph created earlier
    with open("knowledge_graph.json", "r") as f:
        kg = json.load(f)

    # 2) fetch concept info (mimics earlier retrieval component)
    if concept_query not in kg:
        print(f"❌ Concept '{concept_query}' not found in knowledge_graph.json")
        return

    definition = kg[concept_query].get("definition", "Definition not available.")
    related = kg[concept_query].get("related", [])

    # 3) generate slide deck and narration script
    deck, script = generate_slide_deck(concept_query, definition, related, audience_level)

    # 4) save outputs for later use (Manim, presentation, TTS)
    with open("slides.json", "w") as f:
        json.dump(deck, f, indent=4)
    with open("script.txt", "w") as f:
        f.write(script)

    # 5) write minimal Manim file to visualize the first slide (optional)
    manim_file = write_simple_manim(deck, out_path="generated_manim.py")

    # 6) Print a quick preview to the console (so you can show/demo immediately)
    print("✅ Slide deck generated: slides.json")
    print("✅ Narration script saved: script.txt")
    if manim_file:
        print(f"✅ Minimal Manim scene created: {manim_file}")
    print("\n--- Slide preview ---")
    for i, s in enumerate(deck["slides"]):
        print(f"\nSlide {i}: ({s['type']}) {s['title']}")
        if "bullets" in s:
            for b in s["bullets"]:
                print(" -", b)
        if "notes" in s:
            print("Notes:", s["notes"][:200] + ("..." if len(s["notes"])>200 else ""))
    print("\n--- Full narration (first 600 chars) ---\n")
    print(script[:600] + ("..." if len(script)>600 else ""))

# ---------------------------
# If run as script, demonstrate with "Trees"
# ---------------------------
if __name__ == "__main__":
    # Replace "Trees" with any concept present in your knowledge_graph.json
    main("Trees", audience_level="beginner")
