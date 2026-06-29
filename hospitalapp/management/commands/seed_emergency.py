from django.core.management.base import BaseCommand
from hospitalapp.models import EmergencyZone, EmergencyBed

class Command(BaseCommand):
    help = 'Seeds default emergency zones and beds'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding emergency zones...')
        
        zones_data = [
            {
                'zone_name': 'RED',
                'color_code': 'danger',
                'priority_level': 1,
                'target_response_time': 0, # Immediate
            },
            {
                'zone_name': 'ORANGE',
                'color_code': 'orange',
                'priority_level': 2,
                'target_response_time': 15,
            },
            {
                'zone_name': 'YELLOW',
                'color_code': 'warning',
                'priority_level': 3,
                'target_response_time': 60,
            },
            {
                'zone_name': 'GREEN',
                'color_code': 'success',
                'priority_level': 4,
                'target_response_time': 120,
            },
        ]

        zones = {}
        for data in zones_data:
            zone, created = EmergencyZone.objects.get_or_create(
                zone_name=data['zone_name'],
                defaults={
                    'color_code': data['color_code'],
                    'priority_level': data['priority_level'],
                    'target_response_time': data['target_response_time']
                }
            )
            if not created:
                # Update attributes if they already exist
                zone.color_code = data['color_code']
                zone.priority_level = data['priority_level']
                zone.target_response_time = data['target_response_time']
                zone.save()
            zones[data['zone_name']] = zone
            self.stdout.write(f"  Zone {zone.zone_name}: {'Created' if created else 'Updated'}")

        self.stdout.write('Seeding emergency beds...')
        
        beds_data = [
            # RED Zone Beds
            {'bed_number': 'R1', 'zone': 'RED', 'monitor_available': True, 'ventilator_available': True},
            {'bed_number': 'R2', 'zone': 'RED', 'monitor_available': True, 'ventilator_available': True},
            {'bed_number': 'R3', 'zone': 'RED', 'monitor_available': True, 'ventilator_available': False},
            {'bed_number': 'R4', 'zone': 'RED', 'monitor_available': True, 'ventilator_available': False},
            {'bed_number': 'R5', 'zone': 'RED', 'monitor_available': False, 'ventilator_available': False},
            
            # ORANGE Zone Beds
            {'bed_number': 'O1', 'zone': 'ORANGE', 'monitor_available': True, 'ventilator_available': False},
            {'bed_number': 'O2', 'zone': 'ORANGE', 'monitor_available': True, 'ventilator_available': False},
            {'bed_number': 'O3', 'zone': 'ORANGE', 'monitor_available': False, 'ventilator_available': False},
            {'bed_number': 'O4', 'zone': 'ORANGE', 'monitor_available': False, 'ventilator_available': False},
            {'bed_number': 'O5', 'zone': 'ORANGE', 'monitor_available': False, 'ventilator_available': False},
            
            # YELLOW Zone Beds
            {'bed_number': 'Y1', 'zone': 'YELLOW', 'monitor_available': False, 'ventilator_available': False},
            {'bed_number': 'Y2', 'zone': 'YELLOW', 'monitor_available': False, 'ventilator_available': False},
            {'bed_number': 'Y3', 'zone': 'YELLOW', 'monitor_available': False, 'ventilator_available': False},
            {'bed_number': 'Y4', 'zone': 'YELLOW', 'monitor_available': False, 'ventilator_available': False},
            {'bed_number': 'Y5', 'zone': 'YELLOW', 'monitor_available': False, 'ventilator_available': False},
            
            # GREEN Zone Beds
            {'bed_number': 'G1', 'zone': 'GREEN', 'monitor_available': False, 'ventilator_available': False},
            {'bed_number': 'G2', 'zone': 'GREEN', 'monitor_available': False, 'ventilator_available': False},
            {'bed_number': 'G3', 'zone': 'GREEN', 'monitor_available': False, 'ventilator_available': False},
            {'bed_number': 'G4', 'zone': 'GREEN', 'monitor_available': False, 'ventilator_available': False},
            {'bed_number': 'G5', 'zone': 'GREEN', 'monitor_available': False, 'ventilator_available': False},
        ]

        for bed_info in beds_data:
            zone_obj = zones[bed_info['zone']]
            bed, created = EmergencyBed.objects.get_or_create(
                bed_number=bed_info['bed_number'],
                defaults={
                    'zone': zone_obj,
                    'status': 'Available',
                    'monitor_available': bed_info['monitor_available'],
                    'ventilator_available': bed_info['ventilator_available']
                }
            )
            if not created:
                bed.zone = zone_obj
                bed.monitor_available = bed_info['monitor_available']
                bed.ventilator_available = bed_info['ventilator_available']
                bed.save()
            self.stdout.write(f"  Bed {bed.bed_number} ({zone_obj.zone_name}): {'Created' if created else 'Updated'}")
            
        self.stdout.write(self.style.SUCCESS('Successfully seeded emergency zones and beds.'))
