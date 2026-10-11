import json

with open('apps/api/openapi.json', 'r') as f:
    openapi = json.load(f)

markdown = "# MESA Law - Kapsamlı API Endpoint Belgeleri\n\n"
markdown += "Bu belge, sistemde bulunması gereken **tüm API uç noktalarının (endpoints)** mantığını, ne işe yaradıklarını ve Java tarafına taşınırken nelerin yapılması gerektiğini detaylıca açıklamaktadır.\n\n"

# Group endpoints by tags (or paths)
groups = {}
for path, methods in openapi['paths'].items():
    if not path.startswith('/api/v1'):
        continue
    
    for method, details in methods.items():
        tag = details.get('tags', ['Diğer'])[0]
        if tag not in groups:
            groups[tag] = []
        
        groups[tag].append({
            'path': path,
            'method': method.upper(),
            'summary': details.get('summary', 'Özet yok'),
            'description': details.get('description', 'Detaylı açıklama bulunmuyor.'),
        })

# Missing endpoints list (from previous analysis)
missing_endpoints = [
    "GET /api/v1/audit/events",
    "GET /api/v1/deadlines",
    "GET /api/v1/documents",
    "GET /api/v1/documents/matters/{matter_id}",
    "GET /api/v1/documents/{document_id}",
    "GET /api/v1/documents/{document_id}/download",
    "GET /api/v1/documents/{document_id}/viewer-context",
    "GET /api/v1/draft-studio/drafts",
    "GET /api/v1/draft-studio/drafts/matter/{matter_id}",
    "GET /api/v1/draft-studio/drafts/{draft_id}",
    "GET /api/v1/draft-studio/drafts/{draft_id}/citations",
    "GET /api/v1/firms",
    "GET /api/v1/firms/members",
    "GET /api/v1/firms/{firm_id}",
    "GET /api/v1/matters",
    "GET /api/v1/matters/{matter_id}",
    "GET /api/v1/matters/{matter_id}/claims",
    "GET /api/v1/matters/{matter_id}/claims-evidence",
    "GET /api/v1/matters/{matter_id}/evidence",
    "GET /api/v1/matters/{matter_id}/mesa-binding",
    "GET /api/v1/matters/{matter_id}/parties",
    "GET /api/v1/matters/{matter_id}/timeline",
    "GET /api/v1/notifications",
    "GET /api/v1/notifications/sse",
    "GET /api/v1/operations/jobs",
    "GET /api/v1/operations/metrics",
    "GET /api/v1/parser/document/{document_id}",
    "GET /api/v1/parser/{document_id}/pages",
    "GET /api/v1/research/search",
    "GET /api/v1/reviews",
    "GET /api/v1/reviews/{review_id}/context",
    "GET /api/v1/session/context",
    "GET /api/v1/system/dependencies",
    "GET /api/v1/system/settings",
    "GET /api/v1/users/me",
    "POST /api/v1/deadlines/{deadline_id}/complete",
    "POST /api/v1/documents/upload-intent",
    "POST /api/v1/documents/{document_id}/complete",
    "POST /api/v1/draft-studio/drafts",
    "POST /api/v1/draft-studio/drafts/generate",
    "POST /api/v1/draft-studio/drafts/{draft_id}/approve",
    "POST /api/v1/draft-studio/drafts/{draft_id}/export",
    "POST /api/v1/draft-studio/drafts/{draft_id}/submit-review",
    "POST /api/v1/firms",
    "POST /api/v1/matters",
    "POST /api/v1/matters/conflict-check",
    "POST /api/v1/matters/{matter_id}/override-conflict",
    "POST /api/v1/matters/{matter_id}/qa",
    "POST /api/v1/matters/{matter_id}/rebuild-mesa",
    "POST /api/v1/qa/ask",
    "POST /api/v1/research/start",
    "POST /api/v1/reviews/{review_id}/approve",
    "POST /api/v1/reviews/{review_id}/correct",
    "POST /api/v1/reviews/{review_id}/reject",
    "POST /api/v1/session/active-firm",
    "POST /api/v1/system/sync-mesa-core",
    "POST /api/v1/users/me/support-access",
    "PUT /api/v1/draft-studio/drafts/{draft_id}",
    "PUT /api/v1/firms/{firm_id}/members/{user_id}/role",
    "PUT /api/v1/matters/{matter_id}/mesa-binding",
    "PUT /api/v1/system/settings",
    "PUT /api/v1/users/me"
]

def check_if_missing(method, path):
    # normalise slightly to check in the list
    for missing in missing_endpoints:
        m_method, m_path = missing.split(' ')
        # convert {param} to handle matching
        # this is a bit rough but it's just to add a warning badge
        m_path_regex = m_path.replace('{', '[^/]+').replace('}', '') 
        # actually, exact match after stripping param names might be better
        import re
        norm_miss = re.sub(r'\{[^}]+\}', '{}', m_path)
        norm_curr = re.sub(r'\{[^}]+\}', '{}', path)
        if method == m_method and norm_miss == norm_curr:
            return True
    return False

for tag, eps in sorted(groups.items()):
    markdown += f"## {tag}\n\n"
    for ep in eps:
        is_missing = check_if_missing(ep['method'], ep['path'])
        status_badge = "🔴 **[Eksik/Yapılmadı]** " if is_missing else "🟢 **[Java'da Var]** "
        
        markdown += f"### `{ep['method']} {ep['path']}`\n"
        markdown += f"{status_badge}\n\n"
        markdown += f"**Özet:** {ep['summary']}\n\n"
        markdown += f"**Mantık ve Görevi:**\n{ep['description']}\n\n"
        markdown += "---\n"

with open('/Users/mehmetali/.gemini/antigravity-ide/brain/45c85c6e-5770-4dd3-b98c-a13b7af0ac2c/api_endpoints_documentation.md', 'w') as f:
    f.write(markdown)
