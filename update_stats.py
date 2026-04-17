import requests
import os
import re

USERNAME = os.environ.get("USERNAME", "naheunpranto")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

headers = {"Authorization": f"token {TOKEN}"}

query = """
{
  user(login: "%s") {
    repositories(first: 100, ownerAffiliations: OWNER) {
      totalCount
      nodes {
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
    }
  }
}
""" % USERNAME

res = requests.post(
    "https://api.github.com/graphql",
    json={"query": query},
    headers=headers
)
data = res.json()["data"]["user"]

commits = data["contributionsCollection"]["totalCommitContributions"]
repos   = data["repositories"]["totalCount"]
prs     = data["contributionsCollection"]["totalPullRequestContributions"]

# ── Language data ──
lang_sizes  = {}
lang_colors = {}
for repo in data["repositories"]["nodes"]:
    for edge in repo["languages"]["edges"]:
        name  = edge["node"]["name"]
        color = edge["node"]["color"] or "#888888"
        size  = edge["size"]
        lang_sizes[name]  = lang_sizes.get(name, 0) + size
        lang_colors[name] = color

total_size   = sum(lang_sizes.values()) or 1
sorted_langs = sorted(lang_sizes.items(), key=lambda x: x[1], reverse=True)[:5]

# Pad to 5 if fewer than 5 languages
while len(sorted_langs) < 5:
    sorted_langs.append(("N/A", 0))

lang_names = [name for name, _ in sorted_langs]
lang_pcts  = [round(size / total_size * 100) for _, size in sorted_langs]
colors     = [lang_colors.get(name, "#888888") for name in lang_names]

# Ring constants (circumference for r=62, 46, 31)
ring_totals = [390, 289, 195]
ring_offsets = [round(ring_totals[i] * (1 - lang_pcts[i] / 100)) for i in range(3)]

# Bar width (max 430px)
bar_widths = [round(430 * pct / 100) for pct in lang_pcts]

with open("stats.svg", "r") as f:
    svg = f.read()

# ── Update numbers ──
svg = re.sub(r'(<text x="40" y="110"[^>]*>)\d+', rf'\g<1>{commits}', svg)
svg = re.sub(r'(<text x="40" y="174"[^>]*>)\d+', rf'\g<1>{repos}', svg)
svg = re.sub(r'(<text x="40" y="238"[^>]*>)\d+', rf'\g<1>{prs}', svg)

# ── Update ring offsets ──
svg = re.sub(r'(stroke-dashoffset" from="390" to=")\d+', rf'\g<1>{ring_offsets[0]}', svg)
svg = re.sub(r'(stroke-dashoffset" from="289" to=")\d+', rf'\g<1>{ring_offsets[1]}', svg)
svg = re.sub(r'(stroke-dashoffset" from="195" to=")\d+', rf'\g<1>{ring_offsets[2]}', svg)

# ── Update ring colors ──
svg = re.sub(r'(r="62"[^>]*stroke=")[^"#][^"]*(")', rf'\g<1>{colors[0]}\2', svg)
svg = re.sub(r'(r="46"[^>]*stroke=")[^"#][^"]*(")', rf'\g<1>{colors[1]}\2', svg)
svg = re.sub(r'(r="31"[^>]*stroke=")[^"#][^"]*(")', rf'\g<1>{colors[2]}\2', svg)

# ── Update legend colors ──
legend_y = [100, 124, 148, 172, 196]
for i, y in enumerate(legend_y):
    svg = re.sub(
        rf'(<rect x="440" y="{y}"[^>]*fill=")[^"]+(")',
        rf'\g<1>{colors[i]}\2', svg
    )

# ── Update legend names ──
legend_text_y = [109, 133, 157, 181, 205]
for i, y in enumerate(legend_text_y):
    svg = re.sub(
        rf'(<text x="455" y="{y}"[^>]*>)[^<]+(<)',
        rf'\g<1>{lang_names[i]}\2', svg
    )

# ── Update legend percentages ──
for i, y in enumerate(legend_text_y):
    svg = re.sub(
        rf'(<text x="560" y="{y}"[^>]*>)\d+%',
        rf'\g<1>{lang_pcts[i]}%', svg
    )

# ── Update bar names ──
bar_text_y = [342, 357, 372, 387, 402]
for i, y in enumerate(bar_text_y):
    svg = re.sub(
        rf'(<text x="40" y="{y}"[^>]*>)[^<]+(<)',
        rf'\g<1>{lang_names[i]}\2', svg
    )

# ── Update bar fill colors ──
bar_rect_y = [334, 349, 364, 379, 394]
for i, y in enumerate(bar_rect_y):
    svg = re.sub(
        rf'(x="130" y="{y}" width="0"[^>]*fill=")[^"]+(")',
        rf'\g<1>{colors[i]}\2', svg
    )

# ── Update bar widths ──
bar_begin = ["1.2s", "1.3s", "1.4s", "1.5s", "1.6s"]
for i, begin in enumerate(bar_begin):
    svg = re.sub(
        rf'(from="0" to=")\d+(" dur="1\.2s" begin="{begin}")',
        rf'\g<1>{bar_widths[i]}\2', svg
    )

# ── Update bar percentage texts ──
bar_pct_y = [342, 357, 372, 387, 402]
for i, y in enumerate(bar_pct_y):
    svg = re.sub(
        rf'(<text x="572" y="{y}"[^>]*>)\d+%',
        rf'\g<1>{lang_pcts[i]}%', svg
    )

with open("stats.svg", "w") as f:
    f.write(svg)

print(f"✅ Done — commits:{commits} repos:{repos} prs:{prs}")
for i in range(5):
    print(f"   {lang_names[i]}: {lang_pcts[i]}% ({colors[i]})")
