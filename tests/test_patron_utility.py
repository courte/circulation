import datetime
from nose.tools import (
    set_trace, eq_,
    assert_raises,
)

from . import (
    DatabaseTest,
)

from api.util.patron import PatronUtility
from api.circulation_exceptions import *

class TestPatronUtility(DatabaseTest):

    def test_needs_external_sync(self):
        """Test the method that encapsulates the determination
        of whether or not a patron needs to have their account
        synced with the remote.
        """
        now = datetime.datetime.utcnow()
        one_hour_ago = now - datetime.timedelta(hours=1)
        six_seconds_ago = now - datetime.timedelta(seconds=6)
        three_seconds_ago = now - datetime.timedelta(seconds=3)
        yesterday = now - datetime.timedelta(days=1)

        patron = self._patron()
        
        # Patron has never been synced.
        patron.last_external_sync = None
        eq_(True, PatronUtility.needs_external_sync(patron))

        # Patron was synced recently.
        patron.last_external_sync = one_hour_ago
        eq_(False, PatronUtility.needs_external_sync(patron))

        # Patron was synced more than 12 hours ago.
        patron.last_external_sync = yesterday
        eq_(True, PatronUtility.needs_external_sync(patron))

        # Patron was synced recently but has no borrowing
        # privileges. Timeout is five seconds instead of 12 hours.
        patron.authorization_expires = yesterday
        patron.last_external_sync = three_seconds_ago
        eq_(False, PatronUtility.needs_external_sync(patron))

        patron.last_external_sync = six_seconds_ago
        eq_(True, PatronUtility.needs_external_sync(patron))

    def test_has_borrowing_privileges(self):
        """Test the methods that encapsulate the determination
        of whether or not a patron can borrow books.
        """
        now = datetime.datetime.utcnow()
        one_day_ago = now - datetime.timedelta(days=1)

        patron = self._patron()
        eq_(True, PatronUtility.has_borrowing_privileges(patron))
        PatronUtility.assert_borrowing_privileges(patron)
        
        patron.authorization_expires = one_day_ago
        eq_(False, PatronUtility.has_borrowing_privileges(patron))

        assert_raises(
            AuthorizationExpired,
            PatronUtility.assert_borrowing_privileges, patron
        )
        
        # TODO: check excess fines.