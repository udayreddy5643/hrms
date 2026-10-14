<template>
	<BaseLayout :pageTitle="__('Interview Pipeline')">
		<template #body>
			<div class="pipeline-page">
				<header class="pipeline-heading">
					<div>
						<h1>{{ __("Interview Pipeline") }}</h1>
						<p>{{ __("Review applicants and update their latest interview stage.") }}</p>
					</div>
					<Button variant="subtle" :loading="isLoading" @click="reloadData">
						{{ __("Refresh") }}
					</Button>
				</header>

				<div v-if="pageError" class="pipeline-error" role="alert">
					{{ pageError }}
				</div>

				<section class="pipeline-today" :aria-label="__('Today\'s interview counts')">
					<div class="pipeline-today-heading">
						<h2>{{ __("Today's interviews by stage") }}</h2>
						<span v-if="todayCounts.loading">{{ __("Loading…") }}</span>
					</div>
					<div class="pipeline-counts">
						<div v-for="stage in stages" :key="stage" class="pipeline-count">
							<span>{{ stage }}</span>
							<strong>{{ countForStage(stage) }}</strong>
						</div>
					</div>
				</section>

				<div v-if="applicants.loading" class="pipeline-message" role="status">
					{{ __("Loading applicants…") }}
				</div>
				<div v-else-if="!applicants.data?.length" class="pipeline-message">
					{{ __("No applicants are available to display.") }}
				</div>
				<div v-else class="pipeline-board" :aria-label="__('Applicants by pipeline stage')">
					<section v-for="stage in stages" :key="stage" class="pipeline-column">
						<header class="pipeline-column-heading">
							<h2>{{ stage }}</h2>
							<span>{{ applicantsForStage(stage).length }}</span>
						</header>

						<article
							v-for="applicant in applicantsForStage(stage)"
							:key="applicant.name"
							class="pipeline-card"
						>
							<div class="pipeline-card-copy">
								<h3>{{ applicant.applicant_name || applicant.name }}</h3>
								<p v-if="applicant.job_title">{{ applicant.job_title }}</p>
								<p v-if="applicant.email_id">{{ applicant.email_id }}</p>
							</div>
							<label :for="`stage-${applicant.name}`">{{ __("Move to stage") }}</label>
							<select
								:id="`stage-${applicant.name}`"
								:value="draftStages[applicant.name] ?? stage"
								:disabled="savingApplicant === applicant.name"
								@change="setDraftStage(applicant.name, $event.target.value)"
							>
								<option v-for="option in stages" :key="option" :value="option">
									{{ option }}
								</option>
							</select>
							<Button
								variant="subtle"
								class="pipeline-save"
								:loading="savingApplicant === applicant.name"
								:disabled="!hasStageChange(applicant, stage) || Boolean(savingApplicant)"
								@click="saveStage(applicant, stage)"
							>
								{{ __("Save stage") }}
							</Button>
						</article>
						<p v-if="!applicantsForStage(stage).length" class="pipeline-empty-column">
							{{ __("No applicants") }}
						</p>
					</section>
				</div>
			</div>
		</template>
	</BaseLayout>
</template>

<script setup>
import { computed, inject, ref } from "vue"
import { createResource } from "frappe-ui"

import BaseLayout from "@/components/BaseLayout.vue"

const __ = inject("$translate")

const stages = [
	"Screening",
	"Technical Round 1",
	"Technical Round 2",
	"HR Round",
	"Offered",
	"Rejected",
]

const pageError = ref("")
const savingApplicant = ref("")
const draftStages = ref({})

const applicants = createResource({
	url: "frappe.client.get_list",
	params: {
		doctype: "Job Applicant",
		fields: JSON.stringify(["name", "applicant_name", "email_id", "job_title", "pipeline_stage"]),
		filters: JSON.stringify([["docstatus", "!=", 2]]),
		order_by: "modified desc",
		limit_page_length: 200,
	},
	auto: true,
	onError(error) {
		pageError.value = error?.messages?.[0] || error?.message || __("Could not load applicants.")
	},
})

const todayCounts = createResource({
	url: "hrms.hr.doctype.interview.interview.get_pipeline_stage_counts",
	auto: true,
	onError(error) {
		pageError.value = error?.messages?.[0] || error?.message || __("Could not load today's counts.")
	},
})

const isLoading = computed(() => applicants.loading || todayCounts.loading)

function applicantsForStage(stage) {
	return (applicants.data || []).filter((applicant) => (applicant.pipeline_stage || stages[0]) === stage)
}

function countForStage(stage) {
	return todayCounts.data?.find((item) => item.stage === stage)?.count ?? 0
}

function setDraftStage(applicantName, stage) {
	draftStages.value[applicantName] = stage
}

function hasStageChange(applicant, stage) {
	return (draftStages.value[applicant.name] ?? stage) !== stage
}

async function reloadData() {
	pageError.value = ""
	await Promise.all([applicants.reload(), todayCounts.reload()])
}

async function saveStage(applicant, currentStage) {
	const stage = draftStages.value[applicant.name] ?? currentStage
	if (stage === currentStage) return

	pageError.value = ""
	savingApplicant.value = applicant.name
	try {
		const updateStage = createResource({
			url: "hrms.hr.doctype.interview.interview.update_pipeline_stage",
			method: "POST",
		})
		await updateStage.submit({ applicant_id: applicant.name, stage })
		delete draftStages.value[applicant.name]
		await reloadData()
	} catch (error) {
		pageError.value = error?.messages?.[0] || error?.message || __("Could not update the pipeline stage.")
	} finally {
		savingApplicant.value = ""
	}
}
</script>

<style scoped>
.pipeline-page {
	width: 100%;
	max-width: 100%;
	padding: 1.5rem 1rem 2rem;
}

.pipeline-heading,
.pipeline-today-heading,
.pipeline-column-heading {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 1rem;
}

.pipeline-heading h1,
.pipeline-today h2,
.pipeline-column h2,
.pipeline-card h3,
.pipeline-heading p,
.pipeline-card p {
	margin: 0;
}

.pipeline-heading h1 {
	font-size: 1.35rem;
	font-weight: 700;
}

.pipeline-heading p,
.pipeline-card p {
	color: #64748b;
	font-size: 0.875rem;
}

.pipeline-today {
	margin-top: 1.25rem;
	padding: 1rem;
	border: 1px solid #e2e8f0;
	border-radius: 0.75rem;
	background: #fff;
}

.pipeline-today h2 {
	font-size: 1rem;
	font-weight: 600;
}

.pipeline-counts {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr));
	gap: 0.5rem;
	margin-top: 0.75rem;
}

.pipeline-count {
	display: flex;
	justify-content: space-between;
	gap: 0.5rem;
	padding: 0.65rem 0.75rem;
	border-radius: 0.5rem;
	background: #f8fafc;
	font-size: 0.8rem;
}

.pipeline-count strong {
	font-variant-numeric: tabular-nums;
}

.pipeline-board {
	display: grid;
	grid-auto-columns: minmax(17rem, 1fr);
	grid-auto-flow: column;
	gap: 1rem;
	margin-top: 1.25rem;
	padding-bottom: 0.75rem;
	overflow-x: auto;
	align-items: start;
}

.pipeline-column {
	min-height: 12rem;
	padding: 0.75rem;
	border: 1px solid #e2e8f0;
	border-radius: 0.75rem;
	background: #f8fafc;
}

.pipeline-column-heading {
	margin-bottom: 0.75rem;
}

.pipeline-column-heading h2 {
	font-size: 0.9rem;
	font-weight: 650;
}

.pipeline-column-heading span {
	min-width: 1.6rem;
	padding: 0.1rem 0.4rem;
	border-radius: 999px;
	background: #e2e8f0;
	text-align: center;
	font-size: 0.75rem;
}

.pipeline-card {
	display: flex;
	flex-direction: column;
	gap: 0.55rem;
	margin-bottom: 0.65rem;
	padding: 0.75rem;
	border: 1px solid #e2e8f0;
	border-radius: 0.6rem;
	background: #fff;
}

.pipeline-card h3 {
	font-size: 0.9rem;
	font-weight: 600;
}

.pipeline-card-copy p {
	margin-top: 0.2rem;
	overflow-wrap: anywhere;
}

.pipeline-card label {
	font-size: 0.75rem;
	font-weight: 600;
}

.pipeline-card select {
	width: 100%;
	min-height: 2.5rem;
	padding: 0.4rem;
	border: 1px solid #cbd5e1;
	border-radius: 0.4rem;
	background: #fff;
}

.pipeline-save {
	align-self: flex-start;
}

.pipeline-empty-column,
.pipeline-message {
	padding: 1.5rem 0.5rem;
	color: #64748b;
	text-align: center;
	font-size: 0.875rem;
}

.pipeline-error {
	margin-top: 1rem;
	padding: 0.75rem 1rem;
	border: 1px solid #fecaca;
	border-radius: 0.5rem;
	background: #fef2f2;
	color: #b91c1c;
}
</style>
