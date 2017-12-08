##
# Copyright (c) 2017-present MagicStack Inc.
# All rights reserved.
#
# See LICENSE for details.
##


import os.path
import unittest  # NOQA

from edgedb.client import exceptions as exc
from edgedb.server import _testbase as tb


class TestEdgeQLFunctions(tb.QueryTestCase):
    SCHEMA = os.path.join(os.path.dirname(__file__), 'schemas',
                          'issues.eschema')

    SETUP = os.path.join(os.path.dirname(__file__), 'schemas',
                         'issues_setup.eql')

    async def test_edgeql_functions_array_contains_01(self):
        await self.assert_query_result(r'''
            SELECT std::array_contains(<array<int>>[], {1, 3});
            SELECT array_contains([1], {1, 3});
            SELECT array_contains([1, 2], 1);
            SELECT array_contains([1, 2], 3);
            SELECT array_contains(['a'], <std::str>{});
        ''', [
            [False, False],
            [True, False],
            [True],
            [False],
            [],
        ])

    async def test_edgeql_functions_array_contains_02(self):
        await self.assert_query_result('''
            WITH x := [3, 1, 2]
            SELECT array_contains(x, 2);

            WITH x := [3, 1, 2]
            SELECT array_contains(x, 5);

            WITH x := [3, 1, 2]
            SELECT array_contains(x, 5);
        ''', [
            [True],
            [False],
            [False],
        ])

    async def test_edgeql_functions_count_01(self):
        await self.assert_query_result(r"""
            WITH
                MODULE test,
                x := (
                    # User is simply employed as an object to be augmented
                    SELECT User {
                        count := 4,
                        all_issues := Issue
                    } FILTER .name = 'Elvis'
                )
            SELECT x.count = count(x.all_issues);
        """, [
            [True]
        ])

    async def test_edgeql_functions_count_02(self):
        await self.assert_query_result(r"""
            WITH
                MODULE test,
                x := (
                    # User is simply employed as an object to be augmented
                    SELECT User {
                        count := count(Issue),
                        all_issues := Issue
                    } FILTER .name = 'Elvis'
                )
            SELECT x.count = count(x.all_issues);
        """, [
            [True]
        ])

    async def test_edgeql_functions_count_03(self):
        await self.assert_query_result(r"""
            WITH
                MODULE test,
                x := (
                    # User is simply employed as an object to be augmented
                    SELECT User {
                        count := count(<int>Issue.number),
                        all_issues := <int>Issue.number
                    } FILTER .name = 'Elvis'
                )
            SELECT x.count = count(x.all_issues);
        """, [
            [True]
        ])

    async def test_edgeql_functions_array_agg_01(self):
        res = await self.con.execute('''
            SELECT array_agg({1, 2, 3});
            SELECT array_agg({3, 2, 3});
            SELECT array_agg({3, 3, 2});
        ''')
        self.assert_data_shape(res, [
            [[1, 2, 3]],
            [[3, 2, 3]],
            [[3, 3, 2]],
        ])

    @unittest.expectedFailure
    async def test_edgeql_functions_array_agg_02(self):
        res = await self.con.execute('''
            SELECT array_agg({1, 2, 3})[0];
            SELECT array_agg({3, 2, 3})[1];
            SELECT array_agg({3, 3, 2})[-1];
        ''')
        self.assert_data_shape(res, [
            [1],
            [2],
            [2],
        ])

    async def test_edgeql_functions_array_agg_03(self):
        await self.assert_query_result('''
            WITH x := {3, 1, 2}
            SELECT array_agg(x ORDER BY x);

            WITH x := {3, 1, 2}
            SELECT array_agg(x ORDER BY x) = [1, 2, 3];
        ''', [
            [[1, 2, 3]],
            [True],
        ])

    async def test_edgeql_functions_array_agg_04(self):
        await self.assert_query_result('''
            WITH x := {3, 1, 2}
            SELECT array_contains(array_agg(x ORDER BY x), 2);

            WITH x := {3, 1, 2}
            SELECT array_contains(array_agg(x ORDER BY x), 5);

            WITH x := {3, 1, 2}
            SELECT array_contains(array_agg(x ORDER BY x), 5);
        ''', [
            [True],
            [False],
            [False],
        ])

    async def test_edgeql_functions_array_agg_05(self):
        with self.assertRaisesRegex(
                exc.EdgeQLError,
                r'could not determine expression type'):

            await self.con.execute("""
                SELECT array_agg({});
            """)

    async def test_edgeql_functions_array_agg_06(self):
        await self.assert_query_result('''
            SELECT array_agg(<int>{});
            SELECT array_agg(DISTINCT <int>{});
        ''', [
            [
                []
            ],
            [
                []
            ],
        ])

    async def test_edgeql_functions_array_agg_07(self):
        await self.assert_query_result('''
            SELECT array_agg((SELECT schema::Concept FILTER False));
            SELECT array_agg(
                (SELECT schema::Concept FILTER <str>schema::Concept.id = '~')
            );
        ''', [
            [
                []
            ],
            [
                []
            ],
        ])

    async def test_edgeql_functions_array_agg_08(self):
        await self.assert_query_result('''
            WITH x := <int>{}
            SELECT array_agg(x);

            WITH x := (SELECT schema::Concept FILTER False)
            SELECT array_agg(x);

            WITH x := (
                SELECT schema::Concept FILTER <str>schema::Concept.id = '~'
            )
            SELECT array_agg(x);
        ''', [
            [
                []
            ],
            [
                []
            ],
            [
                []
            ],
        ])

    async def test_edgeql_functions_array_agg_09(self):
        await self.assert_query_result(r"""
            WITH MODULE schema
            SELECT
                Concept {
                    l := array_agg(
                        Concept.links.name
                        FILTER
                            Concept.links.name IN {
                                'std::id',
                                'schema::name'
                            }
                        ORDER BY Concept.links.name ASC
                    )
                }
            FILTER
                Concept.name = 'schema::PrimaryClass';
        """, [
            [{
                'l': ['schema::name', 'std::id']
            }]
        ])

    async def test_edgeql_functions_array_agg_10(self):
        await self.assert_query_result(r"""
            WITH MODULE test
            SELECT array_agg(
                [<str>Issue.number, Issue.status.name]
                ORDER BY Issue.number);
        """, [
            [[['1', 'Open'], ['2', 'Open'], ['3', 'Closed'], ['4', 'Closed']]]
        ])

    @unittest.expectedFailure
    async def test_edgeql_functions_array_agg_11(self):
        await self.assert_query_result(r"""
            WITH MODULE test
            SELECT array_agg(
                [<str>Issue.number, Issue.status.name]
                ORDER BY Issue.number)[1];
        """, [
            [['2', 'Open']]
        ])

    async def test_edgeql_functions_array_unpack_01(self):
        await self.assert_query_result(r'''
            SELECT [1, 2];
            SELECT array_unpack([1, 2]);
            SELECT array_unpack([10, 20]) - 1;
        ''', [
            [[1, 2]],
            [1, 2],
            [9, 19],
        ])

    async def test_edgeql_functions_array_enumerate_01(self):
        await self.assert_query_result(r'''
            SELECT [10, 20];
            SELECT array_enumerate([10,20]);
            SELECT array_enumerate([10,20]).1 + 100;
        ''', [
            [[10, 20]],
            [[10, 0], [20, 1]],
            [100, 101],
        ])

    @unittest.expectedFailure
    async def test_edgeql_functions_array_enumerate_02(self):
        # Fix type inference for functions.
        await self.assert_query_result(r'''
            SELECT array_enumerate([10,20]).0 + 100;
        ''', [
            [110, 120],
        ])

    async def test_edgeql_functions_re_match_01(self):
        await self.assert_query_result(r'''
            SELECT re_match('AbabaB', 'ab');
            SELECT re_match('AbabaB', 'AB');
            SELECT re_match('AbabaB', '(?i)AB');
            SELECT re_match('AbabaB', 'ac');

            SELECT EXISTS re_match('AbabaB', 'ac');
            SELECT NOT EXISTS re_match('AbabaB', 'ac');

            SELECT EXISTS re_match('AbabaB', 'ab');
            SELECT NOT EXISTS re_match('AbabaB', 'ab');

            SELECT x := re_match('AbabaB', {'(?i)ab', 'a'}) ORDER BY x;
            SELECT x := re_match({'AbabaB', 'qwerty'}, {'(?i)ab', 'a'})
                ORDER BY x;
        ''', [
            [['ab']],
            [],
            [['Ab']],
            [],

            [False],
            [True],

            [True],
            [False],

            [['Ab'], ['a']],
            [['Ab'], ['a']],
        ])

    async def test_edgeql_functions_re_match_02(self):
        await self.assert_query_result(r'''
            WITH MODULE schema
            SELECT x := re_match(Concept.name, '(\w+)::(Link\w*)')
            ORDER BY x;
        ''', [
            [['schema', 'Link'], ['schema', 'LinkProperty']],
        ])

    async def test_edgeql_functions_re_match_all_01(self):
        await self.assert_query_result(r'''
            SELECT re_match_all('AbabaB', 'ab');
            SELECT re_match_all('AbabaB', 'AB');
            SELECT re_match_all('AbabaB', '(?i)AB');
            SELECT re_match_all('AbabaB', 'ac');

            SELECT EXISTS re_match_all('AbabaB', 'ac');
            SELECT NOT EXISTS re_match_all('AbabaB', 'ac');

            SELECT EXISTS re_match_all('AbabaB', '(?i)ab');
            SELECT NOT EXISTS re_match_all('AbabaB', '(?i)ab');

            SELECT x := re_match_all('AbabaB', {'(?i)ab', 'a'}) ORDER BY x;
            SELECT x := re_match_all({'AbabaB', 'qwerty'}, {'(?i)ab', 'a'})
                ORDER BY x;
        ''', [
            [['ab']],
            [],
            [['Ab'], ['ab'], ['aB']],
            [],

            [False],
            [True],

            [True],
            [False],

            [['Ab'], ['a'], ['a'], ['aB'], ['ab']],
            [['Ab'], ['a'], ['a'], ['aB'], ['ab']],
        ])

    async def test_edgeql_functions_re_match_all_02(self):
        await self.assert_query_result(r'''
            WITH
                MODULE schema,
                C2 := Concept
            SELECT
                count(re_match_all(Concept.name, '(\w+)')) =
                2 * count(C2);
        ''', [
            [True],
        ])

    async def test_edgeql_functions_re_test_01(self):
        await self.assert_query_result(r'''
            SELECT re_test('AbabaB', 'ac');
            SELECT NOT re_test('AbabaB', 'ac');

            SELECT re_test('AbabaB', '(?i)ab');
            SELECT NOT re_test('AbabaB', '(?i)ab');

            # the result always exists
            SELECT EXISTS re_test('AbabaB', '(?i)ac');
            SELECT NOT EXISTS re_test('AbabaB', '(?i)ac');

            SELECT x := re_test('AbabaB', {'ab', 'a'}) ORDER BY x;
            SELECT x := re_test({'AbabaB', 'qwerty'}, {'ab', 'a'}) ORDER BY x;
        ''', [
            [False],
            [True],

            [True],
            [False],

            [True],
            [False],

            [True, True],
            [False, False, True, True],
        ])

    async def test_edgeql_functions_re_test_02(self):
        await self.assert_query_result(r'''
            WITH MODULE schema
            SELECT count(
                Concept FILTER re_test(Concept.name, '(\W\w)bject')
            ) = 1;
        ''', [
            [True],
        ])

    async def test_edgeql_functions_sum_01(self):
        await self.assert_query_result(r'''
            SELECT sum({1, 2, 3, -4, 5});
            SELECT sum({0.1, 0.2, 0.3, -0.4, 0.5});
        ''', [
            [7],
            [0.7],
        ])

    @unittest.expectedFailure
    async def test_edgeql_functions_sum_02(self):
        await self.assert_query_result(r'''
            SELECT sum({1, 2, 3, -4.2, 5});
        ''', [
            [6.8],
        ])
