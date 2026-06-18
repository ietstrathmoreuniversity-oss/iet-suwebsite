from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_galleryitem_photo_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='announcement',
            name='category',
            field=models.CharField(
                choices=[
                    ('Workshop', 'Workshop'),
                    ('Seminar', 'Seminar'),
                    ('Social', 'Social'),
                    ('Competition', 'Competition'),
                    ('Talk', 'Talk'),
                    ('Hackathon', 'Hackathon'),
                    ('General', 'General'),
                ],
                default='General',
                max_length=20,
            ),
        ),
    ]
