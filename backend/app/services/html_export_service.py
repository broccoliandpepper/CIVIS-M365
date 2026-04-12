"""
Service d'export HTML pour les rapports SOC
"""

from datetime import datetime
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class HTMLExportService:
    """Service d'export des rapports SOC en HTML"""
    
    SEVERITY_COLORS = {
        "critical": "#dc2626",  # Red
        "high": "#ea580c",      # Orange Red
        "medium": "#eab308",    # Yellow
        "low": "#22c55e"        # Green
    }
    
    EVENT_TYPE_LABELS = {
        "out-of-list": "Country Anomaly",
        "risk-user": "Risk User Sign-In",
        "fail-spike": "Auth Spike",
        "concurrent-ip": "Concurrent IP"
    }
    
    @staticmethod
    def generate_soc_report(summary: Dict, anomalies: List[Dict], export_request: Any) -> str:
        """Génère le rapport HTML complet"""
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOC Security Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f3f4f6;
            color: #1f2937;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #1e40af 0%, #1f2937 100%);
            color: white;
            padding: 40px 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        
        .header .period {{
            font-size: 14px;
            opacity: 0.9;
        }}
        
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .kpi-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-left: 4px solid #3b82f6;
        }}
        
        .kpi-card.critical {{
            border-left-color: #dc2626;
        }}
        
        .kpi-card.high {{
            border-left-color: #ea580c;
        }}
        
        .kpi-card.medium {{
            border-left-color: #eab308;
        }}
        
        .kpi-card h3 {{
            font-size: 12px;
            text-transform: uppercase;
            color: #6b7280;
            margin-bottom: 10px;
        }}
        
        .kpi-card .value {{
            font-size: 28px;
            font-weight: bold;
            color: #1f2937;
        }}
        
        .kpi-card .subtext {{
            font-size: 12px;
            color: #6b7280;
            margin-top: 8px;
        }}
        
        .section {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 25px;
        }}
        
        .section h2 {{
            font-size: 20px;
            color: #1f2937;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e5e7eb;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        
        th {{
            background: #f3f4f6;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            color: #6b7280;
            border-bottom: 2px solid #e5e7eb;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .badge.critical {{
            background: #fecaca;
            color: #7f1d1d;
        }}
        
        .badge.high {{
            background: #fed7aa;
            color: #7c2d12;
        }}
        
        .badge.medium {{
            background: #fef08a;
            color: #713f12;
        }}
        
        .badge.low {{
            background: #bbf7d0;
            color: #166534;
        }}
        
        .badge.success {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .badge.danger {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .top-countries, .top-users {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 15px;
        }}
        
        .item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .item:last-child {{
            border-bottom: none;
        }}
        
        .item-label {{
            font-weight: 500;
        }}
        
        .item-value {{
            background: #f3f4f6;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e5e7eb;
            font-size: 12px;
            color: #6b7280;
            text-align: center;
        }}
        
        .severity-critical {{ color: #dc2626; }}
        .severity-high {{ color: #ea580c; }}
        .severity-medium {{ color: #eab308; }}
        .severity-low {{ color: #22c55e; }}
        
        .no-data {{
            text-align: center;
            padding: 40px;
            color: #6b7280;
        }}
        
        @media print {{
            body {{ background: white; }}
            .container {{ max-width: 100%; padding: 0; }}
            .section {{ box-shadow: none; border: 1px solid #e5e7eb; page-break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 SOC Security Report</h1>
            <div class="period">
                Period: {summary['start_date']} to {summary['end_date']}<br>
                Generated: {timestamp}
            </div>
        </div>
        
        <div class="kpi-grid">
"""
        
        # Add KPI cards
        kpi_data = [
            ("Total Anomalies", summary['total_anomalies'], "critical" if summary['total_anomalies'] > 10 else "high" if summary['total_anomalies'] > 5 else "medium"),
            ("Critical", summary['critical_count'], "critical"),
            ("High", summary['high_count'], "high"),
            ("Sign-In Events", summary['total_signins'], "medium"),
            ("Failed Rate", f"{summary['failed_rate']}%", "high" if summary['failed_rate'] > 5 else "medium"),
            ("Out-of-List", summary['out_of_list_signins'], "high"),
        ]
        
        for label, value, severity in kpi_data:
            html += f"""
            <div class="kpi-card {severity}">
                <h3>{label}</h3>
                <div class="value">{value}</div>
            </div>
"""
        
        html += """
        </div>
"""
        
        # Anomalies section
        if anomalies:
            html += """
        <div class="section">
            <h2>🚨 Security Anomalies</h2>
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>User</th>
                        <th>Type</th>
                        <th>Severity</th>
                        <th>Country</th>
                        <th>Reason</th>
                    </tr>
                </thead>
                <tbody>
"""
            
            for anomaly in anomalies[:100]:  # Limit to 100 for performance
                severity_badge = f'<span class="badge {anomaly["severity"]}">{anomaly["severity"].upper()}</span>'
                event_type_label = HTMLExportService.EVENT_TYPE_LABELS.get(anomaly['event_type'], anomaly['event_type'])
                timestamp = anomaly['timestamp'][:16] if anomaly['timestamp'] else '-'
                country = anomaly['country'] or '-'
                
                html += f"""
                    <tr>
                        <td>{timestamp}</td>
                        <td>{anomaly['user_principal']}</td>
                        <td>{event_type_label}</td>
                        <td>{severity_badge}</td>
                        <td>{country}</td>
                        <td>{anomaly['reason']}</td>
                    </tr>
"""
            
            html += """
                </tbody>
            </table>
        </div>
"""
        else:
            html += """
        <div class="section">
            <h2>🚨 Security Anomalies</h2>
            <div class="no-data">No anomalies detected during this period ✓</div>
        </div>
"""
        
        # Geographic distribution
        html += """
        <div class="section">
            <h2>🌍 Geographic Distribution</h2>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px;">
                <div>
                    <h3 style="font-size: 16px; margin-bottom: 15px;">Top Countries</h3>
                    <div class="top-countries">
"""
        
        for country, count in list(summary['top_countries'].items())[:10]:
            html += f"""
                        <div class="item">
                            <span class="item-label">{country}</span>
                            <span class="item-value">{count}</span>
                        </div>
"""
        
        html += """
                    </div>
                </div>
                <div>
                    <h3 style="font-size: 16px; margin-bottom: 15px;">Top Users</h3>
                    <div class="top-users">
"""
        
        for user, count in list(summary['top_users'].items())[:10]:
            html += f"""
                        <div class="item">
                            <span class="item-label" title="{user}">{user.split('@')[0]}</span>
                            <span class="item-value">{count}</span>
                        </div>
"""
        
        html += """
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Statistics Summary</h2>
            <table>
                <tr>
                    <td><strong>Allowed Countries</strong></td>
                    <td>BE, SN, BF, BJ, CD, RW, KH, GN, BO, PE</td>
                </tr>
                <tr>
                    <td><strong>Out-of-List Countries</strong></td>
                    <td>""" + ", ".join(summary['out_of_list_countries'] or ['None']) + """</td>
                </tr>
                <tr>
                    <td><strong>Risk Users Sign-Ins</strong></td>
                    <td>""" + str(summary['risk_users_signins']) + """</td>
                </tr>
                <tr>
                    <td><strong>Failed Auth Spikes</strong></td>
                    <td>""" + str(summary['failed_auth_spikes']) + """ (10+ attempts in 5 min)</td>
                </tr>
                <tr>
                    <td><strong>Related Incidents</strong></td>
                    <td>""" + str(summary['related_incidents']) + """</td>
                </tr>
                <tr>
                    <td><strong>Analysis Status</strong></td>
                    <td><span class="badge success">✓ COMPLETED</span></td>
                </tr>
            </table>
        </div>
        
        <div class="footer">
            <p>This report was automatically generated by the SIEM SOC Analysis System.</p>
            <p>Data is real-time and non-anonymized for investigation purposes.</p>
            <p>Generated on """ + timestamp + """</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
