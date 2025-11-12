"""
Django Admin Configuration for SOI Tracking
Add to transparency/admin.py (or create if it doesn't exist)

This implements Ben's workflow:
1. User sees "uncontacted" candidates
2. User manually sends emails
3. User marks as "contacted" in admin
4. User tracks pledge receipts
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from transparency.models import CandidateStatementOfInterest, Office


@admin.register(CandidateStatementOfInterest)
class CandidateSOIAdmin(admin.ModelAdmin):
    """
    Admin interface for manual contact tracking (Phase 1, Req 1b)
    Ben's workflow: User manually sends email, then marks 'contacted'
    """
    
    list_display = [
        'candidate_name_display',
        'office_display',
        'party',
        'email_display',
        'phone',
        'filing_date',
        'status_display',
        'pledge_display',
        'days_since_filing_display',
    ]
    
    list_filter = [
        'contact_status',
        'pledge_received',
        'party',
        'office',
        'filing_date',
    ]
    
    search_fields = [
        'candidate_name',
        'email',
        'phone',
        'office__name',
        'party',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'days_since_filing_display',
        'days_since_contacted_display',
        'source_url_link',
    ]
    
    fieldsets = (
        ('Candidate Information', {
            'fields': (
                'candidate_name',
                'office',
                'party',
                'email',
                'phone',
            )
        }),
        ('SOI Filing', {
            'fields': (
                'filing_date',
                'source_url_link',
                'days_since_filing_display',
            )
        }),
        ('Contact Tracking', {
            'fields': (
                'contact_status',
                'contacted_date',
                'contacted_by',
                'days_since_contacted_display',
            ),
            'description': '✉️ Update contact_status to "contacted" after manually sending info packet'
        }),
        ('Pledge Tracking', {
            'fields': (
                'pledge_received',
                'pledge_received_date',
            ),
            'description': '✅ Check pledge_received when candidate signs pledge'
        }),
        ('Notes & Links', {
            'fields': (
                'notes',
                'entity',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = [
        'mark_as_contacted',
        'mark_pledge_received',
        'mark_no_email',
        'export_uncontacted_emails',
    ]
    
    # Custom display methods
    
    def candidate_name_display(self, obj):
        """Highlight new candidates"""
        if obj.days_since_filing <= 7:
            return format_html(
                '<strong style="color: #0066cc;">🆕 {}</strong>',
                obj.candidate_name
            )
        return obj.candidate_name
    candidate_name_display.short_description = 'Candidate Name'
    candidate_name_display.admin_order_field = 'candidate_name'
    
    def office_display(self, obj):
        """Show office name"""
        return obj.office.name if obj.office else 'Unknown'
    office_display.short_description = 'Office'
    office_display.admin_order_field = 'office__name'
    
    def email_display(self, obj):
        """Show email with warning if missing"""
        if obj.email:
            return obj.email
        return format_html('<span style="color: #cc0000;">⚠️ No Email</span>')
    email_display.short_description = 'Email'
    email_display.admin_order_field = 'email'
    
    def status_display(self, obj):
        """Visual status indicator"""
        if obj.contact_status == 'uncontacted':
            if obj.email:
                return format_html(
                    '<span style="background-color: #ffcccc; padding: 3px 8px; border-radius: 3px; font-weight: bold;">🔴 NEEDS CONTACT</span>'
                )
            else:
                return format_html(
                    '<span style="background-color: #ffeecc; padding: 3px 8px; border-radius: 3px;">⚠️ No Email</span>'
                )
        elif obj.contact_status == 'contacted':
            return format_html(
                '<span style="background-color: #ccffcc; padding: 3px 8px; border-radius: 3px;">✅ Contacted</span>'
            )
        elif obj.contact_status == 'no_email':
            return format_html(
                '<span style="background-color: #eeeeee; padding: 3px 8px; border-radius: 3px;">📭 No Email</span>'
            )
        else:
            return obj.contact_status
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'contact_status'
    
    def pledge_display(self, obj):
        """Visual pledge indicator"""
        if obj.pledge_received:
            return format_html('✅ <strong>Pledged</strong>')
        elif obj.contact_status == 'contacted':
            return format_html('<span style="color: #ff9900;">⏳ Pending</span>')
        else:
            return '-'
    pledge_display.short_description = 'Pledge'
    pledge_display.admin_order_field = 'pledge_received'
    
    def days_since_filing_display(self, obj):
        """Days since SOI filed"""
        days = obj.days_since_filing
        if days <= 7:
            return format_html('🆕 <strong>{} days</strong>', days)
        elif days <= 30:
            return f'{days} days'
        else:
            return f'{days} days (filed {obj.filing_date})'
    days_since_filing_display.short_description = 'Days Since Filing'
    
    def days_since_contacted_display(self, obj):
        """Days since candidate was contacted"""
        days = obj.days_since_contacted
        if days is not None:
            if days <= 14:
                return f'{days} days ago'
            else:
                return f'{days} days ago (contacted {obj.contacted_date})'
        return '-'
    days_since_contacted_display.short_description = 'Days Since Contacted'
    
    def source_url_link(self, obj):
        """Clickable source URL"""
        if obj.source_url:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.source_url, obj.source_url)
        return '-'
    source_url_link.short_description = 'Source URL'
    
    # Bulk actions
    
    def mark_as_contacted(self, request, queryset):
        """Bulk action to mark candidates as contacted"""
        count = queryset.update(
            contact_status='contacted',
            contacted_date=timezone.now().date(),
            contacted_by=request.user.username
        )
        self.message_user(request, f"✅ {count} candidates marked as contacted")
    mark_as_contacted.short_description = "✉️ Mark selected as contacted"
    
    def mark_pledge_received(self, request, queryset):
        """Bulk action to mark pledges received"""
        count = queryset.update(
            pledge_received=True,
            pledge_received_date=timezone.now().date()
        )
        self.message_user(request, f"✅ {count} pledges marked as received")
    mark_pledge_received.short_description = "✅ Mark pledges as received"
    
    def mark_no_email(self, request, queryset):
        """Mark candidates without email"""
        count = queryset.update(contact_status='no_email')
        self.message_user(request, f"📭 {count} candidates marked as 'no email'")
    mark_no_email.short_description = "📭 Mark as 'no email available'"
    
    def export_uncontacted_emails(self, request, queryset):
        """Export email addresses of selected uncontacted candidates"""
        import csv
        from django.http import HttpResponse
        
        # Filter for candidates with emails
        candidates_with_email = queryset.filter(
            contact_status='uncontacted',
            email__isnull=False
        ).exclude(email='')
        
        if not candidates_with_email.exists():
            self.message_user(request, "⚠️ No uncontacted candidates with emails in selection", level='warning')
            return
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="uncontacted_candidates_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Name', 'Email', 'Office', 'Party', 'Phone', 'Filing Date'])
        
        for candidate in candidates_with_email:
            writer.writerow([
                candidate.candidate_name,
                candidate.email,
                candidate.office.name if candidate.office else '',
                candidate.party,
                candidate.phone,
                candidate.filing_date,
            ])
        
        self.message_user(request, f"📧 Exported {candidates_with_email.count()} email addresses")
        return response
    
    export_uncontacted_emails.short_description = "📧 Export email addresses (CSV)"
    
    # Custom queryset
    
    def get_queryset(self, request):
        """Optimize queries with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('office', 'entity')
    
    # Default filters
    
    def changelist_view(self, request, extra_context=None):
        """Show uncontacted candidates by default"""
        if not request.GET.get('contact_status__exact'):
            # If no filter is applied, show uncontacted by default
            extra_context = extra_context or {}
            extra_context['title'] = 'Candidate Statements of Interest (showing Uncontacted)'
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    """Simple admin for Office model"""
    list_display = ['name', 'office_type', 'candidate_count']
    list_filter = ['office_type']
    search_fields = ['name']
    
    def candidate_count(self, obj):
        """Count SOI candidates for this office"""
        count = obj.candidatestatementofinterest_set.count()
        if count > 0:
            url = reverse('admin:transparency_candidatestatementofinterest_changelist') + f'?office__id__exact={obj.office_id}'
            return format_html('<a href="{}">{} candidates</a>', url, count)
        return '0 candidates'
    candidate_count.short_description = 'SOI Candidates'