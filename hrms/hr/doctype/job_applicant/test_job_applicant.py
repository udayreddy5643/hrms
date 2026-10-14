# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and Contributors
# See license.txt

from unittest.mock import MagicMock, patch

import frappe
from frappe.utils import nowdate

from erpnext.setup.doctype.employee.test_employee import make_employee

from hrms.hr.doctype.interview.test_interview import create_interview_type
from hrms.hr.doctype.job_applicant.job_applicant import create_interview, generate_resume_summary
from hrms.hr.doctype.job_applicant.job_applicant import make_employee as map_applicant_to_employee
from hrms.hr.doctype.job_offer.test_job_offer import create_job_offer
from hrms.hr.doctype.job_opening.test_job_opening import get_job_opening
from hrms.tests.test_utils import create_job_applicant
from hrms.tests.utils import HRMSTestSuite, make_user


class TestJobApplicant(HRMSTestSuite):
	def test_generate_resume_summary_uses_openrouter_fallback(self):
		applicant = MagicMock(cover_letter="Experienced Python developer", resume_attachment=None)
		provider_responses = [RuntimeError("Groq unavailable"), "Summary from OpenRouter"]
		with (
			patch("hrms.hr.doctype.job_applicant.job_applicant.frappe.has_permission"),
			patch("hrms.hr.doctype.job_applicant.job_applicant.frappe.get_doc", return_value=applicant),
			patch(
				"hrms.hr.doctype.job_applicant.job_applicant.frappe.conf.get",
				side_effect=lambda key: {"groq_api_key": "groq-test", "openrouter_api_key": "router-test"}.get(key),
			),
			patch(
				"hrms.hr.doctype.job_applicant.job_applicant._request_resume_summary",
				side_effect=provider_responses,
			) as request_summary,
		):
			result = generate_resume_summary("applicant@example.com")

		self.assertEqual(result, "Summary from OpenRouter")
		self.assertEqual(applicant.ai_resume_summary, result)
		applicant.save.assert_called_once_with(ignore_permissions=True)
		self.assertEqual(request_summary.call_args_list[1].args[2], "meta-llama/llama-3.3-70b-instruct")

	def test_generate_resume_summary_reports_both_providers_failed(self):
		applicant = MagicMock(cover_letter="Resume text", resume_attachment=None)
		with (
			patch("hrms.hr.doctype.job_applicant.job_applicant.frappe.has_permission"),
			patch("hrms.hr.doctype.job_applicant.job_applicant.frappe.get_doc", return_value=applicant),
			patch(
				"hrms.hr.doctype.job_applicant.job_applicant.frappe.conf.get",
				side_effect=lambda key: {"groq_api_key": "groq-test", "openrouter_api_key": "router-test"}.get(key),
			),
			patch(
				"hrms.hr.doctype.job_applicant.job_applicant._request_resume_summary",
				side_effect=RuntimeError("provider unavailable"),
			),
		):
			with self.assertRaises(frappe.ValidationError):
				generate_resume_summary("applicant@example.com")

		applicant.save.assert_not_called()

	def test_onload_filters_out_cancelled_job_offer(self):
		applicant = create_job_applicant()
		job_offer = create_job_offer(job_applicant=applicant.name)
		job_offer.submit()
		job_offer.cancel()

		applicant.onload()
		onload = applicant.get("__onload") or {}
		self.assertNotIn("job_offer", onload)

		# positive case: active job offer should be loaded
		active_job_offer = create_job_offer(job_applicant=applicant.name)
		active_job_offer.submit()

		applicant.onload()
		onload = applicant.get("__onload") or {}
		self.assertEqual(onload.get("job_offer"), active_job_offer.name)

	def test_job_applicant_naming(self):
		applicant = frappe.get_doc(
			{
				"doctype": "Job Applicant",
				"status": "Open",
				"applicant_name": "_Test Applicant",
				"email_id": "job_applicant_naming@example.com",
			}
		).insert()
		self.assertEqual(applicant.name, "job_applicant_naming@example.com")

		applicant = frappe.get_doc(
			{
				"doctype": "Job Applicant",
				"status": "Open",
				"applicant_name": "_Test Applicant",
				"email_id": "job_applicant_naming@example.com",
			}
		).insert()
		self.assertEqual(applicant.name, "job_applicant_naming@example.com-1")

	def test_update_applicant_to_employee(self):
		applicant = create_job_applicant()
		job_offer = create_job_offer(
			job_applicant=applicant.name, status="Awaiting Response", company="_Test Company"
		)
		job_offer.save()

		# before creating employee
		self.assertEqual(applicant.status, "Open")
		self.assertEqual(job_offer.status, "Awaiting Response")

		# create employee
		make_employee(user=applicant.name, job_applicant=applicant.name, company="_Test Company")

		# after creating employee
		applicant.reload()
		self.assertEqual(applicant.status, "Accepted")
		job_offer.reload()
		self.assertEqual(job_offer.status, "Accepted")

	def test_make_employee(self):
		opening = get_job_opening(
			job_title="Mapped Applicant Role",
			designation="Software Developer",
			company="_Test Company",
			department="_Test Department - _TC",
		).insert()

		applicant = frappe.get_doc(
			{
				"doctype": "Job Applicant",
				"applicant_name": "Jane Mapped",
				"email_id": "jane.mapped@example.com",
				"phone_number": "1234567890",
				"designation": "Software Developer",
				"job_title": opening.name,
				"currency": "INR",
				"status": "Accepted",
			}
		).insert()

		employee = map_applicant_to_employee(applicant.name)

		self.assertEqual(employee.doctype, "Employee")
		self.assertEqual(employee.job_applicant, applicant.name)
		self.assertEqual(employee.first_name, "Jane Mapped")
		self.assertEqual(employee.employee_name, "Jane Mapped")
		self.assertEqual(employee.personal_email, "jane.mapped@example.com")
		self.assertEqual(employee.cell_number, "1234567890")
		self.assertEqual(employee.designation, "Software Developer")
		self.assertEqual(employee.salary_currency, "INR")
		self.assertEqual(employee.status, "Active")
		self.assertEqual(employee.company, "_Test Company")
		self.assertEqual(employee.department, "_Test Department - _TC")

	def test_create_interview_permission(self):
		applicant = create_job_applicant()
		interviewer = make_user("test_interviewer1@example.com", "Interviewer")
		hr_user = make_user("test_hr_user_interview@example.com", "HR User")
		interview_type = create_interview_type("Technical Round", ["Python"], [interviewer])

		with self.set_user(interviewer):
			self.assertRaises(frappe.PermissionError, create_interview, applicant.name, interview_type.name)

		with self.set_user(hr_user):
			interview = create_interview(applicant.name, interview_type.name)
			self.assertEqual(interview.job_applicant, applicant.name)
