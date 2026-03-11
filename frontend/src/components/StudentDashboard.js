export const StudentDashboard = {
  props: ['state', 'loadStudentDashboard', 'loadEligibleDrives', 'loadApplications', 'applyDrive', 'exportCsv'],
  template: `
    <div class="row g-3">
      <div class="col-lg-4">
        <div class="card glass shadow-sm"><div class="card-body">
          <h5>My Summary</h5>
          <button class="btn btn-primary btn-sm mb-2" @click="loadStudentDashboard">Refresh</button>
          <button class="btn btn-outline-dark btn-sm mb-2 ms-2" @click="exportCsv">Export CSV</button>
          <pre class="bg-light p-3 rounded">{{ state.studentData }}</pre>
        </div></div>
      </div>
      <div class="col-lg-8">
        <div class="card glass shadow-sm"><div class="card-body">
          <div class="d-flex justify-content-between mb-2">
            <h5 class="mb-0">Approved & Eligible Drives</h5>
            <button class="btn btn-primary btn-sm" @click="loadEligibleDrives">Load Drives</button>
          </div>
          <div class="table-responsive">
            <table class="table table-sm align-middle">
              <thead><tr><th>Company</th><th>Role</th><th>Deadline</th><th></th></tr></thead>
              <tbody>
                <tr v-for="d in state.drives" :key="d.drive_id">
                  <td>{{d.company}}</td><td>{{d.job_title}}</td><td>{{d.deadline}}</td>
                  <td><button class="btn btn-success btn-sm" @click="applyDrive(d.drive_id)">Apply</button></td>
                </tr>
              </tbody>
            </table>
          </div>
          <button class="btn btn-outline-primary btn-sm" @click="loadApplications">My Applications</button>
          <pre class="bg-light p-3 rounded mt-2">{{ state.applications }}</pre>
        </div></div>
      </div>
    </div>
  `,
};
