from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_announcement_event_galleryitem_member_official_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='galleryitem',
            name='photo_type',
            field=models.CharField(
                choices=[('header', 'Header Photo'), ('looking_back', 'Looking Back'), ('partners', 'Partners')],
                default='looking_back',
                max_length=20,
            ),
        ),
        migrations.RemoveField(
            model_name='galleryitem',
            name='is_featured',
        ),
    ]
