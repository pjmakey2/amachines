from django.test import TestCase

from OptsIO.mng_user_profile import MUserProfile
from OptsIO.models import UserProfile
from OptsIO.testing import make_business, make_user


class TemaUsuarioTest(TestCase):
    def test_preferencia_de_tema_se_guarda_sin_pisar_otras_y_llega_al_template(self):
        user = make_user('ana', make_business())
        UserProfile.objects.filter(username='ana').update(preferences={'idioma': 'es'})
        mup = MUserProfile()
        self.assertIn('error', mup.set_preference(userobj=user, qdict={'key': 'theme', 'value': 'hacker'}))
        self.assertIn('error', mup.set_preference(userobj=user, qdict={'key': 'is_superuser', 'value': 'true'}))
        self.assertIn('success', mup.set_preference(userobj=user, qdict={'key': 'theme', 'value': 'modern'}))
        self.assertEqual(UserProfile.objects.get(username='ana').preferences, {'idioma': 'es', 'theme': 'modern'})

        self.client.force_login(user)
        html = self.client.get('/io/apps/').content.decode()
        self.assertIn("userTheme: 'modern'", html)
        self.assertIn('amui/am_themes.css', html)
        self.assertIn('amui/am_theme.js', html)
        for vista in ('AMSidebarUi.html', 'AMLauncherUi.html'):
            self.assertIn('am-theme-toggle', self.client.get('/io/dtmpl/', {'tmpl': vista}).content.decode())
