import unittest
from unittest.mock import patch

from hrms.hr.doctype.interview.interview import get_interviewer_list


class TestInterviewerListQuery(unittest.TestCase):
	def test_uses_unique_filters_and_supported_limit(self):
		with patch("hrms.hr.doctype.interview.interview.frappe.get_all", return_value=[]) as get_all:
			get_interviewer_list("User", "uday", "name", 0, 20, {})

		self.assertEqual(
			get_all.call_args.kwargs["filters"],
			[
				["Has Role", "parent", "like", "%uday%"],
				["Has Role", "role", "=", "interviewer"],
				["Has Role", "parenttype", "=", "User"],
			],
		)
		self.assertEqual(get_all.call_args.kwargs["limit"], 20)