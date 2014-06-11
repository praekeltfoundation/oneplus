from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from unittest import skip


class TestContact(TestCase):

    def setUp(self):
        self.client = Client()

    def test_contact_get(self):
        response = self.client.get(reverse("misc.contact"))
        self.assertEqual(response.status_code, 200)

    @skip("View still needs to be implemented")
    def test_contact_post(self):
        response = self.client.post(reverse("misc.contact"), {
            "from": "foo",
            "content": "bar"
        })

        # this will fail because we're not doing any form processing
        # in the view at the moment
        self.assertRedirects(response, reverse("misc.contact"))
