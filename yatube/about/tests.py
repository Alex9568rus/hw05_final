from django.test import TestCase, Client


class StaticPagesURLTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exist_at_disired_location(self):
        testing_dict = {
            self.guest_client.get('/about/author/'): 200,
            self.guest_client.get('/about/tech/'): 200
        }
        for response, value in testing_dict.items():
            with self.subTest(response=response):
                self.assertEqual(response.status_code, value)

    def test_about_yrl_uses_coorect_template(self):
        comparison_dict = {
            self.guest_client.get('/about/author/'): 'about/author.html',
            self.guest_client.get('/about/tech/'): 'about/tech.html'
        }
        for response, value in comparison_dict.items():
            with self.subTest(response=response):
                self.assertTemplateUsed(response, value)
