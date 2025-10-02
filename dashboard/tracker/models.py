from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.utils import timezone


class CustomUserManager(UserManager):
    """Custom user manager that allows login with email"""
    def get_by_natural_key(self, username):
        # Try email first, then username for backwards compatibility
        try:
            return self.get(email__iexact=username)
        except self.model.DoesNotExist:
            return self.get(username=username)


class User(AbstractUser):
    """Custom user model that matches bustimes.org structure"""
    email = models.EmailField(unique=True, verbose_name="email address")
    trusted = models.BooleanField(null=True, help_text="Trusted user status")
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    score = models.IntegerField(null=True, blank=True)

    # Additional fields for migration
    bustimes_id = models.IntegerField(null=True, blank=True, unique=True,
                                      help_text="Original ID from bustimes.org database")

    objects = CustomUserManager()

    USERNAME_FIELD = "email"  # Use email for login like bustimes.org
    REQUIRED_FIELDS = ["username"]  # Keep username for admin compatibility

    class Meta:
        db_table = 'users'


class Route(models.Model):
    """Bus routes information"""
    line_ref = models.CharField(max_length=50, unique=True, help_text="Route identifier")
    published_line_name = models.CharField(max_length=100, help_text="Human-readable route name")
    operator_ref = models.CharField(max_length=20, help_text="Operator NOC code")
    origin_ref = models.CharField(max_length=20, help_text="Origin stop ATCO code")
    destination_ref = models.CharField(max_length=20, help_text="Destination stop ATCO code")
    direction = models.CharField(max_length=20, help_text="Route direction")

    class Meta:
        db_table = 'routes'

    def __str__(self):
        return f"{self.published_line_name} ({self.line_ref})"


class VehiclePosition(models.Model):
    """Vehicle position data for SIRI-VM compliance"""
    OCCUPANCY_CHOICES = [
        ('full', 'Full'),
        ('standingAvailable', 'Standing Available'),
        ('seatsAvailable', 'Seats Available'),
    ]

    vehicle_ref = models.CharField(max_length=50, help_text="Vehicle identifier")
    line_ref = models.CharField(max_length=50, help_text="Route identifier")
    direction_ref = models.CharField(max_length=20, help_text="Journey direction")
    published_line_name = models.CharField(max_length=100, help_text="Route name")
    operator_ref = models.CharField(max_length=20, help_text="Operator code")
    origin_ref = models.CharField(max_length=20, help_text="Origin ATCO code")
    origin_name = models.CharField(max_length=100, help_text="Origin name")
    destination_ref = models.CharField(max_length=20, help_text="Destination ATCO code")
    destination_name = models.CharField(max_length=100, null=True, blank=True, help_text="Destination name")

    # Timetable times
    origin_aimed_departure_time = models.DateTimeField(null=True, blank=True)
    destination_aimed_arrival_time = models.DateTimeField(null=True, blank=True)

    # Location data
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    bearing = models.DecimalField(max_digits=5, decimal_places=2, help_text="Direction in degrees")
    velocity = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Speed in m/s")
    occupancy = models.CharField(max_length=20, choices=OCCUPANCY_CHOICES, null=True, blank=True)

    # Journey info
    block_ref = models.CharField(max_length=50, help_text="Operating block")
    vehicle_journey_ref = models.CharField(max_length=100, help_text="Journey identifier")

    # Timestamps
    recorded_at_time = models.DateTimeField(help_text="When data was recorded")
    valid_until_time = models.DateTimeField(help_text="When data expires")
    item_identifier = models.CharField(max_length=100, null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'vehicle_positions'
        unique_together = ['vehicle_ref', 'recorded_at_time']
        indexes = [
            models.Index(fields=['vehicle_ref']),
            models.Index(fields=['recorded_at_time']),
            models.Index(fields=['longitude', 'latitude']),
        ]

    def __str__(self):
        return f"{self.vehicle_ref} at {self.latitude},{self.longitude}"


class TrackingSession(models.Model):
    """User tracking sessions for self-positioning"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vehicle_ref = models.CharField(max_length=50, help_text="Vehicle being tracked")
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'tracking_sessions'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.user.username} tracking {self.vehicle_ref}"

    def end_session(self):
        """End the tracking session"""
        self.end_time = timezone.now()
        self.is_active = False
        self.save()


class Vehicle(models.Model):
    """Pre-defined vehicles available for tracking"""

    # Core identification (as requested)
    vehicle_unique_ref = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique vehicle identifier (VehicleUniqueRef)"
    )

    # Optional fleet identifier
    fleet_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Fleet number or registration"
    )

    # Status for availability
    is_active = models.BooleanField(
        default=True,
        help_text="Is this vehicle available for tracking?"
    )

    # Last modified tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vehicles'
        ordering = ['vehicle_unique_ref']
        indexes = [
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        display = self.vehicle_unique_ref
        if self.fleet_number:
            display += f" ({self.fleet_number})"
        return display