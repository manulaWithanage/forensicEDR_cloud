"""Plotly report generation module with 5+ visualization types"""
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import Dict, Any, List, Optional
import base64
import io
from motor.motor_asyncio import AsyncIOMotorDatabase


class ReportGenerator:
    """Generate analytical reports with Plotly visualizations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def save_report_to_cache(self, report_type: str, report_data: Dict[str, Any]) -> str:
        """
        Save generated report to database cache
        
        Args:
            report_type: Type of report
            report_data: Complete report data
            
        Returns:
            str: Report ID
        """
        report_id = f"{report_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        cache_entry = {
            "report_id": report_id,
            "report_type": report_type,
            "generated_at": datetime.utcnow(),
            "format": report_data.get('format', 'json'),
            "data": report_data.get('data'),
            "filters": {
                "start_date": report_data.get('start_date'),
                "end_date": report_data.get('end_date')
            },
            "metadata": {
                "total_records": report_data.get('total_records', 0),
                "generated_in_ms": report_data.get('generation_time_ms', 0)
            }
        }
        
        await self.db.cached_reports.insert_one(cache_entry)
        return report_id
    
    async def get_cached_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached report from database
        
        Args:
            report_id: Report identifier
            
        Returns:
            dict or None: Cached report data
        """
        report = await self.db.cached_reports.find_one({'report_id': report_id})
        if report:
            report.pop('_id', None)
        return report
    
    async def get_latest_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most recent cached reports
        
        Args:
            limit: Maximum number of reports to return
            
        Returns:
            list: Recent cached reports
        """
        cursor = self.db.cached_reports.find().sort('generated_at', -1).limit(limit)
        reports = await cursor.to_list(length=limit)
        
        for report in reports:
            report.pop('_id', None)
        
        return reports
    
    async def generate_severity_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate severity distribution pie chart
        
        Returns:
            dict: Plotly figure JSON
        """
        # Build query
        query = {}
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        # Aggregate  by severity
        pipeline = [
            {'$match': query},
            {'$group': {
                '_id': '$severity',
                'count': {'$sum': 1}
            }}
        ]
        
        cursor = self.db.crash_events.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        # Prepare data
        severities = [r['_id'] for r in results]
        counts = [r['count'] for r in results]
        
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=severities,
            values=counts,
            marker=dict(
                colors=['#2ecc71', '#f39c12', '#e74c3c'],  # green, orange, red
            ),
            textinfo='label+percent+value',
            hole=0.3
        )])
        
        fig.update_layout(
            title='Crash Severity Distribution',
            showlegend=True,
            height=500,
            font=dict(size=14)
        )
        
        return fig.to_json()
    
    async def generate_timeline_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate crashes over time line chart
        
        Returns:
            dict: Plotly figure JSON
        """
        # Build query
        query = {}
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        # Get all crashes with timestamps
        cursor = self.db.crash_events.find(query, {'timestamp': 1, 'severity': 1}).sort('timestamp', 1)
        crashes = await cursor.to_list(length=None)
        
        # Group by date
        from collections import defaultdict
        daily_counts = defaultdict(lambda: {'minor': 0, 'moderate': 0, 'severe': 0})
        
        for crash in crashes:
            date = crash['timestamp'].date()
            severity = crash.get('severity', 'unknown')
            if severity in ['minor', 'moderate', 'severe']:
                daily_counts[date][severity] += 1
        
        # Prepare data
        dates = sorted(daily_counts.keys())
        minor = [daily_counts[d]['minor'] for d in dates]
        moderate = [daily_counts[d]['moderate'] for d in dates]
        severe = [daily_counts[d]['severe'] for d in dates]
        
        # Create line chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates, y=minor,
            name='Minor',
            mode='lines+markers',
            line=dict(color='#2ecc71', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=dates, y=moderate,
            name='Moderate',
            mode='lines+markers',
            line=dict(color='#f39c12', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=dates, y=severe,
            name='Severe',
            mode='lines+markers',
            line=dict(color='#e74c3c', width=2)
        ))
        
        fig.update_layout(
            title='Crashes Over Time',
            xaxis_title='Date',
            yaxis_title='Number of Crashes',
            hovermode='x unified',
            height=500
        )
        
        return fig.to_json()
    
    async def generate_geographic_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate geographic crash locations scatter map
        
        Returns:
            dict: Plotly figure JSON
        """
        # Build query
        query = {}
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        # Get all crashes with locations
        cursor = self.db.crash_events.find(
            query,
            {'event_id': 1, 'location': 1, 'severity': 1, 'crash_type': 1}
        )
        crashes = await cursor.to_list(length=None)
        
        # Prepare data
        lats = []
        lons = []
        severities = []
        event_ids = []
        crash_types = []
        
        for crash in crashes:
            if 'location' in crash and 'coordinates' in crash['location']:
                coords = crash['location']['coordinates']
                lons.append(coords[0])  # longitude
                lats.append(coords[1])  # latitude
                severities.append(crash.get('severity', 'unknown'))
                event_ids.append(crash.get('event_id', 'N/A'))
                crash_types.append(crash.get('crash_type', 'unknown'))
        
        # Color mapping
        color_map = {'minor': '#2ecc71', 'moderate': '#f39c12', 'severe': '#e74c3c'}
        colors = [color_map.get(s, '#95a5a6') for s in severities]
        
        # Create scatter mapbox
        fig = go.Figure(go.Scattermapbox(
            lat=lats,
            lon=lons,
            mode='markers',
            marker=dict(
                size=12,
                color=colors,
                opacity=0.7
            ),
            text=[f"{eid}<br>{ct}<br>{sev}" for eid, ct, sev in zip(event_ids, crash_types, severities)],
            hovertemplate='<b>%{text}</b><br>Lat: %{lat}<br>Lon: %{lon}<extra></extra>'
        ))
        
        # Set map center (Colombo, Sri Lanka as default)
        center_lat = sum(lats) / len(lats) if lats else 6.9271
        center_lon = sum(lons) / len(lons) if lons else 79.8612
        
        fig.update_layout(
            title='Geographic Crash Distribution',
            mapbox=dict(
                style='open-street-map',
                center=dict(lat=center_lat, lon=center_lon),
                zoom=10
            ),
            height=600,
            showlegend=False
        )
        
        return fig.to_json()
    
    async def generate_crash_type_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate crash type breakdown bar chart
        
        Returns:
            dict: Plotly figure JSON
        """
        # Build query
        query = {}
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        # Aggregate by crash type
        pipeline = [
            {'$match': query},
            {'$group': {
                '_id': '$crash_type',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ]
        
        cursor = self.db.crash_events.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        # Prepare data
        crash_types = [r['_id'].replace('_', ' ').title() for r in results]
        counts = [r['count'] for r in results]
        
        # Create bar chart
        fig = go.Figure(data=[go.Bar(
            x=crash_types,
            y=counts,
            marker=dict(
                color=['#3498db', '#9b59b6', '#e67e22', '#1abc9c'],
                line=dict(color='rgba(0,0,0,0.3)', width=1)
            ),
            text=counts,
            textposition='auto'
        )])
        
        fig.update_layout(
            title='Crash Type Breakdown',
            xaxis_title='Crash Type',
            yaxis_title='Number of Crashes',
            height=500,
            showlegend=False
        )
        
        return fig.to_json()
    
    async def generate_impact_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate impact force vs severity scatter plot
        
        Returns:
            dict: Plotly figure JSON
        """
        # Build query
        query = {}
        if start_date or end_date:
            query['timestamp'] = {}
            if start_date:
                query['timestamp']['$gte'] = start_date
            if end_date:
                query['timestamp']['$lte'] = end_date
        
        # Get crashes with impact data
        cursor = self.db.crash_events.find(
            query,
            {'severity': 1, 'calculated_values.impact_force_g': 1, 
             'calculated_values.total_acceleration': 1, 'crash_type': 1}
        )
        crashes = await cursor.to_list(length=None)
        
        # Prepare data
        impact_forces = []
        total_accel = []
        severities = []
        crash_types = []
        
        for crash in crashes:
            if 'calculated_values' in crash:
                calc = crash['calculated_values']
                if 'impact_force_g' in calc:
                    impact_forces.append(calc['impact_force_g'])
                    total_accel.append(calc.get('total_acceleration', 0))
                    severities.append(crash.get('severity', 'unknown'))
                    crash_types.append(crash.get('crash_type', 'unknown'))
        
        # Color mapping
        color_map = {'minor': '#2ecc71', 'moderate': '#f39c12', 'severe': '#e74c3c'}
        colors = [color_map.get(s, '#95a5a6') for s in severities]
        
        # Create scatter plot
        fig = go.Figure(data=[go.Scatter(
            x=total_accel,
            y=impact_forces,
            mode='markers',
            marker=dict(
                size=10,
                color=colors,
                opacity=0.6,
                line=dict(width=1, color='rgba(0,0,0,0.3)')
            ),
            text=[f"{ct}<br>{sev}" for ct, sev in zip(crash_types, severities)],
            hovertemplate='<b>%{text}</b><br>Total Accel: %{x:.2f} m/s²<br>Impact Force: %{y:.2f}g<extra></extra>'
        )])
        
        fig.update_layout(
            title='Impact Force vs Total Acceleration',
            xaxis_title='Total Acceleration (m/s²)',
            yaxis_title='Impact Force (g)',
            height=500,
            showlegend=False
        )
        
        return fig.to_json()
    
    async def generate_report(
        self,
        report_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        format: str = 'json',
        save_to_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generate report based on type and optionally cache it
        
        Args:
            report_type: Type of report (severity, timeline, geographic, crash_type, impact)
            start_date: Optional start date filter
            end_date: Optional end date filter
            format: Export format (json, html, png)
            save_to_cache: Whether to save report to database cache
            
        Returns:
            dict: Report data with metadata including report_id if cached
        """
        import time
        start_time = time.time()
        
        # Generate report based on type
        if report_type == 'severity':
            fig_json = await self.generate_severity_report(start_date, end_date)
        elif report_type == 'timeline':
            fig_json = await self.generate_timeline_report(start_date, end_date)
        elif report_type == 'geographic':
            fig_json = await self.generate_geographic_report(start_date, end_date)
        elif report_type == 'crash_type':
            fig_json = await self.generate_crash_type_report(start_date, end_date)
        elif report_type == 'impact':
            fig_json = await self.generate_impact_report(start_date, end_date)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        generation_time = int((time.time() - start_time) * 1000)  # ms
        
        # Return based on format
        report_data = None
        if format == 'json':
            report_data = {
                'report_type': report_type,
                'generated_at': datetime.utcnow(),
                'format': 'json',
                'data': fig_json,
                'start_date': start_date,
                'end_date': end_date,
                'generation_time_ms': generation_time
            }
        elif format == 'html':
            import json
            fig = go.Figure(json.loads(fig_json))
            html = fig.to_html(include_plotlyjs='cdn')
            report_data = {
                'report_type': report_type,
                'generated_at': datetime.utcnow(),
                'format': 'html',
                'data': html,
                'start_date': start_date,
                'end_date': end_date,
                'generation_time_ms': generation_time
            }
        elif format == 'png':
            import json
            fig = go.Figure(json.loads(fig_json))
            img_bytes = fig.to_image(format='png', width=1200, height=800)
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            report_data = {
                'report_type': report_type,
                'generated_at': datetime.utcnow(),
                'format': 'png',
                'data': f'data:image/png;base64,{img_base64}',
                'start_date': start_date,
                'end_date': end_date,
                'generation_time_ms': generation_time
            }
        
        # Save to cache if requested
        if save_to_cache and report_data:
            report_id = await self.save_report_to_cache(report_type, report_data)
            report_data['report_id'] = report_id
            report_data['cached'] = True
        else:
            report_data['cached'] = False
        
        return report_data
