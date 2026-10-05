from datetime import datetime
from zoneinfo import ZoneInfo

from django.db import migrations


def seed(apps, schema_editor):
    Event = apps.get_model("events", "Event")
    rows = [
        (6, 'Круглый стол «Навыки сильного разработчика в эпоху ИИ»', 'Круглый стол, 2 ч.',
         'Александр Ковалёв\nАлександр Полищук\nСурен Хоренян\nМихаил Васильев',
         'Обсуждаем, что важно для разработчика в эпоху ИИ', '4201922'),
        (9, 'Круглый стол «Навыки сильного разработчика в эпоху ИИ»', 'Круглый стол, 2 ч.',
         'Алексей Жиряков\nМаксим Богуславский\nДенис Аникин\nНиколай Хитров',
         'Обсуждаем, что важно для разработчика в эпоху ИИ', '4202016'),
        (23, 'Воркшоп «Безопасная разработка с ИИ + ИИ для безопасной разработки»',
         'Воркшоп, 2 ч.', 'Александр Ковалёв\nМаксим Богуславский',
         'Совместно решаем проблемы безопасной разработки с ИИ', '4229889'),
    ]
    for day, title, format_, speakers, description, registration in rows:
        Event.objects.using(schema_editor.connection.alias).create(
            title=title, starts_at=datetime(2026, 10, day, 19, tzinfo=ZoneInfo("Europe/Moscow")),
            format=format_, speakers=speakers, short_description=description,
            registration_url=f"https://moscowdjango.timepad.ru/event/{registration}/",
        )


class Migration(migrations.Migration):
    dependencies = [("events", "0001_initial")]
    # Preserve organizer-edited records if the seed migration is rolled back.
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
