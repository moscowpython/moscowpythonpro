from django.db import migrations


def seed(apps, schema_editor):
    Resident = apps.get_model("landing", "Resident")
    rows = [
        ("Александр Ковалёв", "Ozon Tech", "Руководитель группы разработки",
         "Делает платформу контактов и коммуникаций SyncUp. Участвует в программном комитете конференции «Импульс», выступает на митапах и конференциях. Тот самый человек с блокнотом из первого ряда, который задаёт вопросы спикерам.",
         "https://alkov.pro/"),
        ("Александр Полищук", "МТС Веб Сервисы", "Руководитель разработки Дата платформы",
         "В разработке более 10 лет. Развивает каталог данных и процессы разработки в MWS Data. Спикер HighLoad и Moscow Python, член программного комитета True Tech.", ""),
        ("Алексей Жиряков", "Сбер", "Исполнительный директор в дивизионе «Развитие генеративного ИИ»",
         "Отвечает за работу с данными и платформу сбора в GenAI. Более 15 лет в backend-разработке и управлении инженерными командами; ранее — CTO стрима онлайн-кинотеатра KION. Член программных комитетов HighLoad++ и AI Native Conf.", ""),
        ("Максим Богуславский", "ООО «Альфа-функция»", "Генеральный директор",
         "Более 20 лет в IT, из них более 10 — на руководящих позициях. Занимается кибербезопасностью, импортозамещением и AI-first архитектурой. Выступает на TeamLead Conf, Moscow Python и CodeFest.", "https://t.me/aiscepticism"),
        ("Михаил Васильев", "Райффайзенбанк", "Старший инженер по машинному обучению",
         "Разрабатывает и внедряет ML- и AI-решения в банковском и enterprise-сегменте. Создаёт production-системы с LLM, NLP, Computer Vision и классическим машинным обучением. Ведёт ML-проекты от discovery до внедрения и оценки результата.", "https://onixlas.github.io/"),
        ("Сурен Хоренян", "Яндекс", "Старший разработчик",
         "Python-разработчик, руководитель команды и open-source contributor. Преподаёт веб-разработку с 2018 года, создаёт образовательные программы и обучает команды компаний. Постоянный спикер Moscow Python Meetup.", "https://mahenzon.ru/"),
        ("Денис Аникин", "Райффайзенбанк", "Техлид",
         "Руководит командой, которая строит AI-платформу с LLM и RAG. Занимается архитектурой, code review, backend, frontend и DevOps. Основал и развивает Python-сообщество внутри банка.", "https://xfenix.ru/"),
        ("Николай Хитров", "Точка Банк", "Тимлид",
         "Пишет enterprise-приложения на Python. Продвигает DDD, функциональное программирование и практики разработки сложных проектов. Спикер PyCon, PiterPy и отраслевых митапов: об архитектуре Python-приложений и безопасности.", ""),
    ]
    for order, (name, company, position, bio, website) in enumerate(rows, 1):
        Resident.objects.using(schema_editor.connection.alias).create(
            name=name, company=company, position=position, bio=bio, website=website, order=order,
        )


class Migration(migrations.Migration):
    dependencies = [("landing", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
