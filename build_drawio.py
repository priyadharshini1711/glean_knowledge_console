#!/usr/bin/env python3
"""Generates the Glean production architecture .drawio (mxfile) diagram."""
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

nodes = {}   # id -> dict(x,y,w,h,label,style,parent)
edges = []   # (id, source, target, label, style)
_id_counter = [1]

def nid():
    _id_counter[0] += 1
    return f"id{_id_counter[0]}"

def node(label, x, y, w, h, style, parent="1"):
    i = nid()
    nodes[i] = dict(x=x, y=y, w=w, h=h, label=label, style=style, parent=parent)
    return i

def edge(src, tgt, label="", style="", eid=None):
    i = eid or nid()
    edges.append((i, src, tgt, label, style))
    return i

# ---------- styles ----------
BASE = "rounded=1;whiteSpace=wrap;html=1;fontSize=11;arcSize=12;shadow=0;"
S_SOURCE   = BASE + "fillColor=#FFE6CC;strokeColor=#D79B00;"
S_INGEST   = BASE + "fillColor=#DAE8FC;strokeColor=#6C8EBF;"
S_IDENTITY = BASE + "fillColor=#F8CECC;strokeColor=#B85450;"
S_GATEWAY  = BASE + "fillColor=#FFF2CC;strokeColor=#D6B656;"
S_COMPUTE  = BASE + "fillColor=#D5E8D4;strokeColor=#82B366;"
S_GLEAN    = BASE + "fillColor=#E1D5E7;strokeColor=#9673A6;fontStyle=1;"
S_OBS      = BASE + "fillColor=#F5F5F5;strokeColor=#666666;"
S_CICD     = BASE + "fillColor=#FFF2CC;strokeColor=#B8860B;"
S_CLIENT   = BASE + "fillColor=#FFFFFF;strokeColor=#000000;"
S_DLQ      = BASE + "fillColor=#F8CECC;strokeColor=#B85450;"

CONTAINER = ("rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#666666;"
             "dashed=1;verticalAlign=top;fontSize=14;fontStyle=1;align=left;"
             "spacingLeft=10;spacingTop=8;")

TITLE_STYLE = "text;html=1;fontSize=22;fontStyle=1;align=left;verticalAlign=middle;"
SUB_STYLE = "text;html=1;fontSize=12;fontStyle=2;align=left;verticalAlign=middle;fontColor=#666666;"

E_SOLID  = "edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;fontSize=9;strokeColor=#666666;"
E_DASH   = E_SOLID + "dashed=1;"
E_SEC    = E_SOLID + "strokeColor=#B85450;"
E_OBS    = E_SOLID + "strokeColor=#999999;dashed=1;"
E_CICD   = E_SOLID + "strokeColor=#B8860B;"

# =========================================================
# Title
# =========================================================
node("Glean Enterprise RAG Chatbot &#8212; Production Architecture on Azure",
     40, 10, 900, 30, TITLE_STYLE)
node("Secure, CI/CD-enabled, SOC 2-aligned deployment for 5,000 employees / 3 business units",
     40, 42, 900, 20, SUB_STYLE)

# =========================================================
# Row 0: Clients / End Users
# =========================================================
c_clients = node("End Users &amp; Clients", 40, 80, 480, 110, CONTAINER)
n_employees = node("Employees\n(Web Chat UI)\nFinance / Eng / HR", 60, 110, 140, 70, S_CLIENT, c_clients)
n_mcp_client = node("MCP Clients\n(Cursor / Claude Desktop)", 220, 110, 140, 70, S_CLIENT, c_clients)
n_bu_admin = node("BU Admins\n(read-only dashboard)", 380, 110, 120, 70, S_CLIENT, c_clients)

# =========================================================
# Row 0b: External Data Sources (top right)
# =========================================================
c_sources = node("External Data Sources", 560, 80, 480, 110, CONTAINER)
n_sp = node("SharePoint / OneDrive\n(Microsoft Graph API)", 580, 110, 130, 70, S_SOURCE, c_sources)
n_conf = node("Confluence\n(REST connector)", 720, 110, 110, 70, S_SOURCE, c_sources)
n_fs = node("File Shares\n(Azure Data Factory)", 840, 110, 110, 70, S_SOURCE, c_sources)
n_hr = node("HR / Ticketing Systems\n(webhooks)", 700, 190, 0, 0, S_SOURCE, "1")  # placeholder replaced below
del nodes[n_hr]
c_sources2 = node("", 560, 80, 0, 0, S_SOURCE, "1")
del nodes[c_sources2]
n_hr = node("HR / Ticketing\n(Event Grid webhooks)", 960, 110, 130, 70, S_SOURCE, c_sources)

# =========================================================
# Row 1: Identity & Secrets (right column)
# =========================================================
c_identity = node("Identity &amp; Secrets Management", 1560, 80, 340, 340, CONTAINER)
n_entra = node("Microsoft Entra ID\nSAML 2.0 / OIDC SSO\nissues short-lived JWT (1hr)", 1580, 115, 300, 70, S_IDENTITY, c_identity)
n_keyvault = node("Azure Key Vault\nGlean tokens, API keys,\nTLS certs — auto-rotated 90d", 1580, 200, 300, 70, S_IDENTITY, c_identity)
n_managed_id = node("Azure Managed Identity\n(no static credentials for\nContainer Apps / Functions)", 1580, 285, 300, 70, S_IDENTITY, c_identity)
n_defender = node("Microsoft Defender for Cloud\n(continuous posture: CIS/NIST/ISO)", 1580, 350, 300, 60, S_IDENTITY, c_identity)

# =========================================================
# Row 2: Ingestion & Processing
# =========================================================
c_ingest = node("Ingestion &amp; Processing Layer", 40, 220, 1000, 220, CONTAINER)
n_blob = node("Azure Blob Storage\n(landing zone)", 60, 255, 130, 65, S_INGEST, c_ingest)
n_eventgrid = node("Azure Event Grid\nblob-created trigger +\ndaily 2AM re-sync timer", 210, 255, 150, 65, S_INGEST, c_ingest)
n_svcbus = node("Azure Service Bus Queue\n(decouples ingestion bursts\nfrom query traffic)", 380, 255, 160, 65, S_INGEST, c_ingest)
n_func = node("Azure Functions\n(extract text, apply metadata,\ncall Indexing API) — concurrency cap 100", 560, 255, 200, 65, S_COMPUTE, c_ingest)
n_dlq = node("Dead-Letter Queue\n(DLQ) — failed docs\n+ retry / alert", 780, 255, 140, 65, S_DLQ, c_ingest)
n_scale = node("Scale: 50k docs ≈ 14 docs/sec/hr | lock duration 5min + exponential backoff", 60, 335, 860, 40, "text;html=1;fontSize=10;fontStyle=2;fontColor=#666666;align=left;", c_ingest)

# =========================================================
# Row 3: Azure VNet Application Perimeter
# =========================================================
c_vnet = node("Azure VNet — Application Perimeter (private subnets)", 40, 460, 1000, 300, CONTAINER)
n_appgw = node("Application Gateway + WAF\n(public entry, TLS 1.2+ termination)", 60, 500, 170, 65, S_GATEWAY, c_vnet)
n_apim = node("Azure API Management\n(JWT validation, rate limiting,\nAPI contract)", 260, 500, 170, 65, S_GATEWAY, c_vnet)
n_natgw = node("Azure NAT Gateway\n(outbound egress to\nGlean SaaS APIs)", 830, 500, 170, 65, S_GATEWAY, c_vnet)
n_containerapp = node("Azure Container Apps\nFastAPI Chat Service\n(auto-scale 2-20 replicas, KEDA)", 60, 590, 190, 70, S_COMPUTE, c_vnet)
n_mcp_server = node("Azure Container Apps\nMCP Server\n(search + chat tools)", 280, 590, 180, 70, S_COMPUTE, c_vnet)
n_redis = node("Azure Cache for Redis\n(cache search/chat results\n15 min TTL, ~40% API call cut)", 490, 590, 190, 70, S_GATEWAY, c_vnet)
n_privend = node("Private Endpoints\n(Key Vault, Blob, Service Bus)", 720, 590, 170, 70, S_GATEWAY, c_vnet)

# =========================================================
# Row 4: Glean Platform (SaaS, tenant-isolated)
# =========================================================
c_glean = node("Glean Platform — SaaS, Tenant-Isolated (SOC 2 Type II)", 1130, 460, 480, 220, CONTAINER)
n_idx_api = node("Glean Indexing API", 1150, 500, 200, 55, S_GLEAN, c_glean)
n_search_api = node("Glean Search API", 1150, 565, 200, 55, S_GLEAN, c_glean)
n_chat_api = node("Glean Chat API\n(grounded answers + citations)", 1150, 630, 200, 55, S_GLEAN, c_glean)
n_glean_tenant = node("Glean Tenant Data Store\n(permission-aware index:\nallowedUsers / allowedGroups)", 1370, 550, 220, 90, S_GLEAN, c_glean)

# =========================================================
# Row 5: Observability & Compliance
# =========================================================
c_obs = node("Observability, Audit &amp; Compliance", 40, 800, 1570, 190, CONTAINER)
n_monitor = node("Azure Monitor\n(metrics, action groups)", 60, 835, 160, 65, S_OBS, c_obs)
n_loganalytics = node("Log Analytics Workspace\n(7-yr retention, IAM-scoped export)", 240, 835, 180, 65, S_OBS, c_obs)
n_appinsights = node("Application Insights\n(distributed tracing,\ntime-to-first-token)", 440, 835, 170, 65, S_OBS, c_obs)
n_pagerduty = node("PagerDuty\nP1 if error rate &gt;5% / 2min", 630, 835, 160, 65, S_OBS, c_obs)
n_dashboard = node("Azure Dashboard\n(customer read-only:\nhealth, uptime, volume by BU)", 810, 835, 180, 65, S_OBS, c_obs)
n_auditlog = node("App Audit Log\n(Entra user ID, query,\ndocs returned — every request)", 1010, 835, 190, 65, S_OBS, c_obs)
n_sla = node("SLA: 99.9% uptime  |  24-hr post-mortems  |  weekly usage &amp; error email", 60, 915, 1140, 40, "text;html=1;fontSize=10;fontStyle=2;fontColor=#666666;align=left;", c_obs)

# =========================================================
# Row 6: CI/CD Pipeline
# =========================================================
c_cicd = node("CI/CD Pipeline — Infrastructure &amp; Application Delivery", 40, 1020, 1570, 220, CONTAINER)
n_git = node("Git Repo\n(GitHub / Azure Repos)\nfeature branch + PR", 60, 1060, 150, 65, S_CICD, c_cicd)
n_ci_build = node("CI: Build &amp; Unit Tests\n(GitHub Actions /\nAzure Pipelines)", 230, 1060, 150, 65, S_CICD, c_cicd)
n_sec_scan = node("Security Gates\nSAST/DAST, Trivy/Snyk image scan,\nCheckov IaC scan, secret scan", 400, 1060, 190, 65, S_CICD, c_cicd)
n_acr = node("Azure Container\nRegistry (ACR)\nimage signed &amp; pushed", 610, 1060, 150, 65, S_CICD, c_cicd)
n_iac = node("Terraform / Bicep\nIaC apply\n(plan reviewed → apply)", 780, 1060, 160, 65, S_CICD, c_cicd)
n_deploy_stg = node("Deploy to Staging\n(Container Apps revision)\n+ smoke tests", 960, 1060, 170, 65, S_CICD, c_cicd)
n_gate = node("Manual Approval Gate\n(release owner sign-off)", 1150, 1060, 160, 65, S_CICD, c_cicd)
n_deploy_prod = node("Deploy to Production\n(blue/green traffic split,\nauto-rollback on failure)", 1330, 1060, 190, 65, S_CICD, c_cicd)
n_cicd_note = node("Same pipeline provisions Key Vault, VNet, APIM, Container Apps, Redis via IaC — no manual console changes in prod",
                    60, 1145, 1500, 35, "text;html=1;fontSize=10;fontStyle=2;fontColor=#666666;align=left;", c_cicd)

# =========================================================
# Legend
# =========================================================
c_legend = node("Legend", 1220, 80, 340, 340, CONTAINER)
ly = 115
legend_items = [
    ("Client / End User", S_CLIENT),
    ("External Data Source", S_SOURCE),
    ("Ingestion Component", S_INGEST),
    ("Identity / Secrets", S_IDENTITY),
    ("Network / Gateway / Cache", S_GATEWAY),
    ("Compute (Container Apps / Functions)", S_COMPUTE),
    ("Glean SaaS (managed)", S_GLEAN),
    ("Observability", S_OBS),
    ("CI/CD Stage", S_CICD),
]
for label, style in legend_items:
    node("", 1240, ly, 20, 20, style, c_legend)
    node(label, 1268, ly, 280, 20, "text;html=1;fontSize=11;align=left;verticalAlign=middle;", c_legend)
    ly += 27

# =========================================================
# Edges
# =========================================================
edge(n_sp, n_blob, "sync", E_SOLID)
edge(n_conf, n_blob, "sync", E_SOLID)
edge(n_fs, n_blob, "copy", E_SOLID)
edge(n_hr, n_svcbus, "webhook", E_SOLID)
edge(n_blob, n_eventgrid, "blob created", E_SOLID)
edge(n_eventgrid, n_svcbus, "event", E_SOLID)
edge(n_svcbus, n_func, "dequeue", E_SOLID)
edge(n_func, n_idx_api, "index docs", E_SOLID)
edge(n_svcbus, n_dlq, "failed msg", E_DASH)
edge(n_dlq, n_pagerduty, "alert", E_OBS)

edge(n_employees, n_appgw, "HTTPS", E_SOLID)
edge(n_mcp_client, n_appgw, "HTTPS (MCP)", E_SOLID)
edge(n_bu_admin, n_dashboard, "view", E_DASH)
edge(n_appgw, n_apim, "", E_SOLID)
edge(n_apim, n_containerapp, "route", E_SOLID)
edge(n_apim, n_mcp_server, "route (MCP)", E_SOLID)
edge(n_entra, n_apim, "JWT validation", E_SEC)
edge(n_employees, n_entra, "SSO login", E_SEC)
edge(n_containerapp, n_redis, "cache check", E_SOLID)
edge(n_mcp_server, n_redis, "cache check", E_SOLID)
edge(n_containerapp, n_search_api, "search", E_SOLID)
edge(n_containerapp, n_chat_api, "chat", E_SOLID)
edge(n_mcp_server, n_search_api, "search tool", E_SOLID)
edge(n_mcp_server, n_chat_api, "chat tool", E_SOLID)
edge(n_search_api, n_glean_tenant, "", E_SOLID)
edge(n_chat_api, n_glean_tenant, "", E_SOLID)
edge(n_idx_api, n_glean_tenant, "", E_SOLID)
edge(n_containerapp, n_natgw, "egress", E_DASH)
edge(n_func, n_natgw, "egress", E_DASH)
edge(n_managed_id, n_keyvault, "fetch secret", E_SEC)
edge(n_containerapp, n_managed_id, "identity", E_SEC)
edge(n_func, n_managed_id, "identity", E_SEC)
edge(n_privend, n_keyvault, "private link", E_DASH)

# observability edges
for src in [n_appgw, n_apim, n_containerapp, n_mcp_server, n_func]:
    edge(src, n_loganalytics, "", E_OBS)
edge(n_loganalytics, n_monitor, "", E_OBS)
edge(n_loganalytics, n_appinsights, "", E_OBS)
edge(n_loganalytics, n_auditlog, "", E_OBS)
edge(n_monitor, n_pagerduty, "alert", E_OBS)
edge(n_monitor, n_dashboard, "metrics", E_OBS)
edge(n_defender, n_containerapp, "posture scan", E_OBS)

# CI/CD edges
edge(n_git, n_ci_build, "", E_CICD)
edge(n_ci_build, n_sec_scan, "", E_CICD)
edge(n_sec_scan, n_acr, "", E_CICD)
edge(n_acr, n_iac, "", E_CICD)
edge(n_iac, n_deploy_stg, "", E_CICD)
edge(n_deploy_stg, n_gate, "", E_CICD)
edge(n_gate, n_deploy_prod, "", E_CICD)
edge(n_deploy_prod, n_containerapp, "deploys", E_CICD + "curved=1;")
edge(n_iac, c_vnet, "provisions", E_CICD + "dashed=1;curved=1;")

# =========================================================
# Build mxfile XML
# =========================================================
mxfile = ET.Element("mxfile", {"host": "app.diagrams.net", "modified": "2026-07-13T00:00:00.000Z",
                                "agent": "Claude", "version": "24.7.0", "type": "device"})
diagram = ET.SubElement(mxfile, "diagram", {"id": "arch-page-1", "name": "1 - Production Architecture"})
model = ET.SubElement(diagram, "mxGraphModel", {
    "dx": "1400", "dy": "800", "grid": "1", "gridSize": "10", "guides": "1", "tooltips": "1",
    "connect": "1", "arrows": "1", "fold": "1", "page": "1", "pageScale": "1",
    "pageWidth": "1950", "pageHeight": "1300", "math": "0", "shadow": "0"
})
root = ET.SubElement(model, "root")
ET.SubElement(root, "mxCell", {"id": "0"})
ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

for i, d in nodes.items():
    cell = ET.SubElement(root, "mxCell", {
        "id": i, "value": d["label"], "style": d["style"],
        "vertex": "1", "parent": d["parent"]
    })
    ET.SubElement(cell, "mxGeometry", {
        "x": str(d["x"]), "y": str(d["y"]), "width": str(d["w"]), "height": str(d["h"]),
        "as": "geometry"
    })

for i, src, tgt, label, style in edges:
    cell = ET.SubElement(root, "mxCell", {
        "id": i, "value": label, "style": style,
        "edge": "1", "parent": "1", "source": src, "target": tgt
    })
    ET.SubElement(cell, "mxGeometry", {"relative": "1", "as": "geometry"})

xml_str = ET.tostring(mxfile, encoding="unicode")
out_path = "/sessions/outputs/Glean_Production_Architecture.drawio"
with open("Glean_Production_Architecture.drawio", "w", encoding="utf-8") as f:
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write(xml_str)

print("Nodes:", len(nodes), "Edges:", len(edges))
print("Written to Glean_Production_Architecture.drawio")
