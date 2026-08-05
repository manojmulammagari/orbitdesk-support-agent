"""
Generate a PNG diagram of the agent graph architecture.
Run: python graph_diagram.py
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

fig, ax = plt.subplots(1, 1, figsize=(10, 12))
ax.set_xlim(0, 10)
ax.set_ylim(0, 14)
ax.axis('off')

# Title
ax.text(5, 13.5, 'OrbitDesk Support Agent - Graph Architecture', 
        fontsize=16, fontweight='bold', ha='center')
ax.text(5, 13.1, 'LangGraph + Local Hugging Face Models', 
        fontsize=10, ha='center', color='gray')

def draw_node(ax, x, y, width, height, text, color, text_color='white'):
    box = FancyBboxPatch((x - width/2, y - height/2), width, height,
                         boxstyle="round,pad=0.05,rounding_size=0.2",
                         facecolor=color, edgecolor='black', linewidth=1.5)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=9, 
            fontweight='bold', color=text_color, wrap=True)
    return (x, y + height/2)

def draw_arrow(ax, start, end, label=None, color='black'):
    arrow = FancyArrowPatch(start, end,
                           arrowstyle='->', mutation_scale=15,
                           color=color, linewidth=1.5,
                           connectionstyle="arc3,rad=0.1")
    ax.add_patch(arrow)
    if label:
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        ax.text(mid_x + 0.3, mid_y, label, fontsize=7, color='darkblue', style='italic')

# Nodes (top to bottom)
nodes = [
    (5, 12.0, 'START', '#2c3e50'),
    (5, 10.8, 'TRIAGE\n(Embedding Classifier)', '#e74c3c'),
    (5, 9.0, 'RETRIEVE\n(Sentence-Transformers)', '#3498db'),
    (5, 7.2, 'GENERATE\n(TinyLlama LLM)', '#9b59b6'),
    (5, 5.4, 'VERIFY\n(Grounding Check)', '#f39c12'),
    (5, 3.6, 'REVISE\n(Retry Context)', '#1abc9c'),
    (5, 1.8, 'FINALIZE\n(JSON Output)', '#27ae60'),
    (5, 0.5, 'END', '#2c3e50'),
]

# Side nodes for conditional paths
side_nodes = [
    (2, 9.0, 'GENERATE\n(Clarify)', '#95a5a6'),
    (8, 9.0, 'GENERATE\n(Out-of-scope)', '#95a5a6'),
]

# Draw main nodes
positions = {}
for x, y, text, color in nodes:
    top = draw_node(ax, x, y, 2.8, 0.9, text, color)
    positions[text.split('\n')[0]] = (x, y)

# Draw side nodes
for x, y, text, color in side_nodes:
    draw_node(ax, x, y, 2.2, 0.8, text, color, text_color='black')

# Draw arrows
draw_arrow(ax, (5, 12.4), (5, 11.3))  # START -> TRIAGE

# TRIAGE branches
draw_arrow(ax, (5, 10.4), (5, 9.4), 'answerable/escalation')
draw_arrow(ax, (3.7, 10.4), (2, 9.4), 'clarification')
draw_arrow(ax, (6.3, 10.4), (8, 9.4), 'out_of_scope')

# Main flow
draw_arrow(ax, (5, 8.6), (5, 7.6))   # RETRIEVE -> GENERATE
draw_arrow(ax, (5, 6.8), (5, 5.8))   # GENERATE -> VERIFY

# VERIFY branches
draw_arrow(ax, (5, 5.0), (5, 4.0), 'passed')   # VERIFY -> FINALIZE
draw_arrow(ax, (6.3, 5.0), (6.3, 3.6), 'failed')  # VERIFY -> REVISE
draw_arrow(ax, (6.3, 3.6), (6.3, 7.2), 'retry')   # REVISE -> GENERATE (loop)

# Side paths to FINALIZE
draw_arrow(ax, (2, 8.6), (3.7, 2.0))   # GENERATE(clarify) -> FINALIZE
draw_arrow(ax, (8, 8.6), (6.3, 2.0))   # GENERATE(oos) -> FINALIZE

# FINALIZE -> END
draw_arrow(ax, (5, 1.4), (5, 0.9))

# Add loop-back arrow for revise (curved)
from matplotlib.patches import Arc
arc = Arc((6.8, 5.4), 1.2, 4.0, angle=0, theta1=90, theta2=270, 
          color='#1abc9c', linewidth=2, linestyle='--')
ax.add_patch(arc)
ax.annotate('', xy=(6.3, 7.2), xytext=(6.3, 3.6),
            arrowprops=dict(arrowstyle='->', color='#1abc9c', lw=2, ls='--'))
ax.text(7.5, 5.4, 'retry loop\n(max 1)', fontsize=7, color='#1abc9c', ha='center')

# Add legend box
legend_text = """Key Features:
• Shared Typed State (AgentState)
• Conditional Routing (triage → 4 paths)
• Retry Loop (verify → revise → generate)
• Loop Protection (retry_count ≤ 1)
• Deterministic + Model-based hybrid"""

ax.text(0.3, 0.3, legend_text, fontsize=8, va='bottom',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

plt.tight_layout()
plt.savefig('graph_diagram.png', dpi=150, bbox_inches='tight', 
            facecolor='white', edgecolor='none')
print("✓ Graph diagram saved to graph_diagram.png")
plt.show()
