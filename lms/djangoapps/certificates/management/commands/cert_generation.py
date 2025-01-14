"""
Management command to generate course certificates for one or more users in a given course run.
"""

import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.certificates.generation_handler import generate_certificate_task

User = get_user_model()
log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to generate course certificates for one or more users in a given course run.

    Example usage:
    ./manage.py lms cert_generation -u 123 456 -c course-v1:edX+DemoX+Demo_Course
    """

    help = """
    Generate course certificates for one or more users in a given course run.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-u', '--user',
            nargs='+',
            metavar='USER',
            dest='user',
            required=True,
            help='user_id or space-separated list of user_ids for whom to generate course certificates'
        )
        parser.add_argument(
            '-c', '--course-key',
            metavar='COURSE_KEY',
            dest='course_key',
            required=True,
            help='course run key'
        )

    def handle(self, *args, **options):
        if not options.get('user'):
            raise CommandError('You must specify a list of users')

        course_key = options.get('course_key')
        if not course_key:
            raise CommandError('You must specify a course-key')

        # Parse the serialized course key into a CourseKey
        try:
            course_key = CourseKey.from_string(course_key)
        except InvalidKeyError as e:
            raise CommandError('You must specify a valid course-key') from e

        # Loop over each user, and ask that a cert be generated for them
        users_str = options['user']
        for user_id in users_str:
            user = None
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                log.warning('User {user} could not be found'.format(user=user_id))
            if user is not None:
                log.info(
                    'Calling generate_certificate_task for {user} : {course}'.format(
                        user=user.id,
                        course=course_key
                    ))
                generate_certificate_task(user, course_key)
