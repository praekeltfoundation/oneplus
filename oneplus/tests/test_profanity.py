from communication.utils import contains_profanity
from django.test import TestCase


class ProfanityTests(TestCase):
    fixtures = ['profanities.json']

    def test_profanities(self):
        contents = [
            "hellow boo",
            "What guys",
            "teboho...I have made the administrator aware of system failure....but also please lets us be careful on "
            "what we say....it should be all about maths and qwaqwa, tshiya maths from mr mdlalose",
            "no teboho",
            "Since I'm new in one plus but I have proved that this is the way to success in pro maths 2015.",
            "Since I'm new in one plus but I have proved that this is the way to success in pro maths.",
            "how is everyone doing with eucliean geometry grade 11?",
            "hmmm.....i think about it more than i forget ......i didnt practise the whole week last week and its "
            "something i am not proud of......but then i shall try my best ....",
            "Mine doesn't want to work. It keeps saying I should come tomorrow but tomorrow never comes. "
            "What should I do?",
            "What do I do if it doesn't want me to login everyday",
            "how did you deal with today's challenges",
            "How do u wim airtime ?",
            "hi im momelezi a maths student in kutlwanong",
            "yho your questions are tricky but they are good for us ''cause they open our minds",
            "thank u for revisions that u have given US",
            "revision and practise could not be any easy and effective as it is with oneplus. Guys do spread the "
            "world as better individuals we can make better friends, with better friends better school mates, with "
            "better school mates, with better school mates better schools, with better schools better communities, "
            "with better communities better countries, with better countries a better world. With a better world a "
            "better Future. Isn't that great?"
        ]
        for content in contents:
            self.assertEquals(contains_profanity(content), False, content)
