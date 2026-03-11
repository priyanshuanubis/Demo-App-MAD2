export const CompanyDashboard = {
  props: ['state', 'loadDashboard', 'loadDrives', 'loadApplications', 'createDrive'],
  template: `
    <div class="row g-3">
      <div class="col-lg-6">
        <div class="card glass shadow-sm"><div class="card-body">
          <h5>Company Dashboard</h5>
          <div class="d-flex gap-2 mb-2">
            <button class="btn btn-primary btn-sm" @click="loadDashboard">Refresh</button>
            <button class="btn btn-outline-primary btn-sm" @click="loadDrives">Drives</button>
            <button class="btn btn-outline-primary btn-sm" @click="loadApplications">Applications</button>
          </div>
          <pre class="bg-light p-3 rounded">{{ state.companyData }}</pre>
        </div></div>
      </div>
      <div class="col-lg-6">
        <div class="card glass shadow-sm"><div class="card-body">
          <h5>Create Placement Drive</h5>
          <input v-model="state.drive.job_title" class="form-control mb-2" placeholder="Job title" />
          <textarea v-model="state.drive.job_description" class="form-control mb-2" placeholder="Job description"></textarea>
          <div class="row g-2 mb-2">
            <div class="col"><input v-model="state.drive.eligible_branch" class="form-control" placeholder="Eligible branch" /></div>
            <div class="col"><input v-model="state.drive.eligible_year" class="form-control" placeholder="Eligible year" /></div>
          </div>
          <div class="row g-2 mb-3">
            <div class="col"><input v-model="state.drive.min_cgpa" class="form-control" placeholder="Min CGPA" /></div>
            <div class="col"><input v-model="state.drive.application_deadline" type="date" class="form-control" /></div>
          </div>
          <button class="btn btn-success w-100" @click="createDrive">Create Drive</button>
        </div></div>
      </div>
    </div>
  `,
};
