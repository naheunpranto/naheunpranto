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
        languages(first: 5, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
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

lang_sizes = {}
for repo in data["repositories"]["nodes"]:
    for edge in repo["languages"]["edges"]:
        name = edge["node"]["name"]
        size = edge["size"]
        lang_sizes[name] = lang_sizes.get(name, 0) + size

total_size = sum(lang_sizes.values()) or 1
sorted_langs = sorted(lang_sizes.items(), key=lambda x: x[1], reverse=True)[:3]
lang_pcts = {name: round(size / total_size * 100) for name, size in sorted_langs}
lang_names = [name for name, _ in sorted_langs]

pct1 = lang_pcts.get(lang_names[0], 0) if len(lang_names) > 0 else 0
pct2 = lang_pcts.get(lang_names[1], 0) if len(lang_names) > 1 else 0
pct3 = lang_pcts.get(lang_names[2], 0) if len(lang_names) > 2 else 0

ring1_offset = round(427 * (1 - pct1 / 100))
ring2_offset = round(314 * (1 - pct2 / 100))
ring3_offset = round(207 * (1 - pct3 / 100))
bar1_width   = round(460 * pct1 / 100)
bar2_width   = round(460 * pct2 / 100)

with open("stats.svg", "r") as f:
    svg = f.read()

svg = re.sub(r'(<text x="40" y="110"[^>]*>)\d+', rf'\g<1>{commits}', svg)
svg = re.sub(r'(<text x="40" y="174"[^>]*>)\d+', rf'\g<1>{repos}', svg)
svg = re.sub(r'(<text x="40" y="238"[^>]*>)\d+', rf'\g<1>{prs}', svg)

svg = re.sub(r'(stroke-dashoffset" from="427" to=")\d+', rf'\g<1>{ring1_offset}', svg)
svg = re.sub(r'(stroke-dashoffset" from="314" to=")\d+', rf'\g<1>{ring2_offset}', svg)
svg = re.sub(r'(stroke-dashoffset" from="207" to=")\d+', rf'\g<1>{ring3_offset}', svg)

svg = re.sub(r'(attributeName="width" from="0" to=")\d+(" dur="1.2s" begin="1.2s")', rf'\g<1>{bar1_width}\2', svg)
svg = re.sub(r'(attributeName="width" from="0" to=")\d+(" dur="1.2s" begin="1.4s")', rf'\g<1>{bar2_width}\2', svg)

with open("stats.svg", "w") as f:
    f.write(svg)

print(f"✅ Done — commits:{commits} repos:{repos} prs:{prs}")
print(f"   {lang_names[0] if lang_names else '?'}:{pct1}% | {lang_names[1] if len(lang_names)>1 else '?'}:{pct2}% | {lang_names[2] if len(lang_names)>2 else '?'}:{pct3}%")
