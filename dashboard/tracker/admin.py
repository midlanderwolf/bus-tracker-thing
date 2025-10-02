from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import Vehicle, TrackingSession, VehiclePosition

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = [
        'vehicle_unique_ref',
        'fleet_number',
        'is_active',
        'updated_at'
    ]

    list_filter = ['is_active']
    search_fields = ['vehicle_unique_ref', 'fleet_number']

    fieldsets = (
        ('Vehicle Identification', {
            'fields': ('vehicle_unique_ref', 'fleet_number')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']


@admin.register(TrackingSession)
class TrackingSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'vehicle_ref', 'start_time', 'end_time', 'is_active', 'duration', 'position_count']
    list_filter = ['is_active', 'start_time', 'end_time', 'user']
    search_fields = ['vehicle_ref', 'user__email', 'user__username']
    actions = ['end_sessions', 'delete_sessions_with_positions']
    readonly_fields = ['start_time']

    def duration(self, obj):
        if obj.end_time and obj.start_time:
            duration = obj.end_time - obj.start_time
            return f"{duration.total_seconds() / 3600:.1f}h"
        elif obj.is_active:
            duration = timezone.now() - obj.start_time
            return f"{duration.total_seconds() / 3600:.1f}h (active)"
        return "N/A"
    duration.short_description = "Duration"

    def position_count(self, obj):
        from .models import VehiclePosition
        return VehiclePosition.objects.filter(
            vehicle_ref=obj.vehicle_ref,
            recorded_at_time__gte=obj.start_time,
            recorded_at_time__lte=obj.end_time or timezone.now()
        ).count()
    position_count.short_description = "Positions"

    def end_sessions(self, request, queryset):
        """End selected active tracking sessions"""
        updated = queryset.filter(is_active=True).update(
            is_active=False,
            end_time=timezone.now()
        )
        self.message_user(request, f"Successfully ended {updated} tracking sessions.")

    def delete_sessions_with_positions(self, request, queryset):
        """Delete sessions and all associated vehicle positions"""
        session_count = queryset.count()
        position_count = 0

        for session in queryset:
            # Delete positions within session timeframe
            deleted, _ = VehiclePosition.objects.filter(
                vehicle_ref=session.vehicle_ref,
                recorded_at_time__gte=session.start_time,
                recorded_at_time__lte=session.end_time or timezone.now()
            ).delete()
            position_count += deleted

        # Delete sessions
        queryset.delete()

        self.message_user(
            request,
            f"Successfully deleted {session_count} sessions and {position_count} vehicle positions."
        )

    end_sessions.short_description = "End selected tracking sessions"
    delete_sessions_with_positions.short_description = "Delete sessions and associated positions"


@admin.register(VehiclePosition)
class VehiclePositionAdmin(admin.ModelAdmin):
    list_display = [
        'vehicle_ref',
        'line_ref',
        'operator_ref',
        'recorded_at_time',
        'coordinates',
        'direction_ref',
        'occupancy'
    ]
    list_filter = [
        'recorded_at_time',
        'operator_ref',
        'line_ref',
        'direction_ref',
        'occupancy'
    ]
    search_fields = ['vehicle_ref', 'line_ref', 'operator_ref', 'origin_name', 'destination_name']
    readonly_fields = ['recorded_at_time', 'created_at', 'valid_until_time']
    actions = ['delete_old_positions', 'delete_vehicle_tracks', 'delete_operator_data']
    list_per_page = 50

    def coordinates(self, obj):
        return format_html(
            '<a href="https://www.google.com/maps?q={},{}" target="_blank">{:.6f}, {:.6f}</a>',
            obj.latitude, obj.longitude, obj.latitude, obj.longitude
        )
    coordinates.short_description = "Coordinates"

    def get_queryset(self, request):
        # Limit to recent positions for performance (last 7 days)
        return super().get_queryset(request).filter(
            recorded_at_time__gte=timezone.now() - timezone.timedelta(days=7)
        ).order_by('-recorded_at_time')

    def delete_old_positions(self, request, queryset):
        """Delete positions older than 30 days"""
        cutoff = timezone.now() - timezone.timedelta(days=30)
        deleted, _ = VehiclePosition.objects.filter(
            recorded_at_time__lt=cutoff
        ).delete()
        self.message_user(request, f"Deleted {deleted} vehicle positions older than 30 days.")

    def delete_vehicle_tracks(self, request, queryset):
        """Delete all positions for selected vehicles"""
        vehicle_refs = set(queryset.values_list('vehicle_ref', flat=True))
        deleted = 0
        for ref in vehicle_refs:
            count, _ = VehiclePosition.objects.filter(vehicle_ref=ref).delete()
            deleted += count
        self.message_user(request, f"Deleted {deleted} positions for {len(vehicle_refs)} vehicles.")

    def delete_operator_data(self, request, queryset):
        """Delete all positions for selected operators"""
        operator_refs = set(queryset.values_list('operator_ref', flat=True))
        deleted = 0
        for ref in operator_refs:
            count, _ = VehiclePosition.objects.filter(operator_ref=ref).delete()
            deleted += count
        self.message_user(request, f"Deleted {deleted} positions for {len(operator_refs)} operators.")

    delete_old_positions.short_description = "Delete positions older than 30 days"
    delete_vehicle_tracks.short_description = "Delete all tracks for selected vehicles"
    delete_operator_data.short_description = "Delete all data for selected operators"