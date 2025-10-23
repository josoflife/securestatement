import os
import sys
import traceback
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'securefiles.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from statements.models import Statement
from django.utils import timezone

User = get_user_model()

try:
    username = 'testbot'
    password = 'TestPass123'
    user, created = User.objects.get_or_create(username=username)
    if created:
        user.set_password(password)
        user.save()
        print('Created test user')
    else:
        print('Test user exists')

    client = Client()
    # prefer force_login to bypass auth backend issues
    client.force_login(user)

    today = date.today()
    start = (today - timedelta(days=7)).isoformat()
    end = today.isoformat()

    print('Posting generate with', start, end)
    resp = client.post('/generate/', {'start_date': start, 'end_date': end}, follow=True)
    print('Generate POST status:', resp.status_code)

    # Find latest statement for user
    stmt = Statement.objects.filter(user=user).order_by('-created_at').first()
    if not stmt:
        print('No Statement record found')
        sys.exit(2)

    print('Found statement:', stmt.id, stmt.pdf, 'token:', stmt.token[:20], 'expiry:', stmt.token_expiry)

    # Try to download via client
    download_url = f'/statements/download/{stmt.token}/'
    print('Attempting GET', download_url)
    dl = client.get(download_url)
    print('Download status:', dl.status_code)
    if dl.status_code == 200:
        out_path = os.path.join('scripts', f'downloaded_statement_{stmt.id}.pdf')
        with open(out_path, 'wb') as f:
            f.write(dl.content)
        print('Saved downloaded PDF to', out_path)
        print('Size bytes:', os.path.getsize(out_path))
    else:
        print('Download response content:', dl.content[:500])

except Exception as e:
    print('EXCEPTION')
    traceback.print_exc()
    sys.exit(3)

print('Done')
