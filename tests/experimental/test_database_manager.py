from doctest import DocTestRunner, DocTestFinder, OutputChecker
import unittest
import sys

# -- Module --

from library.objectmodels import (
    subcategory,
    relationships,
    alusers,
    db,
)

# -- Globals --

class docTester(OutputChecker):
    """checker subclass that overrides "check_output" to return an object from
    the doctest string representation.
    """

    def check_output(self, want, got, optionflags):
        self.formation = self._toAscii(got)
        return OutputChecker.check_output(self, want, got, optionflags)


class testDatabase(unittest.TestCase):

    def setUp(self):
        self.subcategory = testObj(subcategory)
        #self.relationship = testObj(relationships)
        self.user = testObj(alusers)

    def tearDown(self):
        qApp.quit()

    def test_objectmodels(self):
        """Classes inheriting BaseFields from "objectmodels" module.
        """
        return
        self.assertIsInstance(self.subcategory.name, str)
        self.assertIsInstance(self.subcategory.category, int)
        self.assertEqual(self.relationship.category, 'test')
        self.assertEqual(self.relationship.category_id, 0)

    def test_subcategoryRoundTrip(self):
        return
        self.subcategory.create()
        self.assertIsInstance(self.subcategory.id, int)
        self.subcategory.name = 'test_update'
        self.subcategory.update()
        
        # Update specific fields
        self.subcategory.name = 'test_parent'
        self.subcategory.count = 4
        self.subcategory.update(fields=['name', 'count'])


        child_subcategory = subcategory(link=self.subcategory.id, name='test_child')
        child_subcategory.create()

        # Test values as tuple / arrays
        #multi_subcategory = subcategory(name=('test_multi',), category=(1,))
        #multi_subcategory.create()

        for x in (self.subcategory, child_subcategory):#, multi_subcategory):
            x.remove()

    #def test_assetRoundTrip(self):
    #    pass
    #    #self.assertRaises(NotImplementedError, self.db.checkAssetExists, None, None)

    def test_users(self):
        pass


def testObj(obj):
    test = DocTestFinder().find(obj)[0]
    check = docTester()
    runner = DocTestRunner(verbose=False, checker=check)
    #print(test.name, '->', runner.run(test))
    runner.run(test)
    obj = eval(check.formation[1:][:-2])
    return obj


if __name__ == "__main__":
    unittest.main()
    sys.exit(app.exec_())
