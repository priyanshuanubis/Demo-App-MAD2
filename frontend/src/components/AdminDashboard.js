export const AdminDashboard = {
  props: ['state', 'reloadStats', 'loadCompanies', 'loadStudents', 'search'],
  template: `
    <div class="row g-3">
      <div class="col-lg-4" v-for="(v,k) in state.stats" :key="k">
        <div class="card glass shadow-sm"><div class="card-body">
          <p class="small-muted text-uppercase mb-1">{{k}}</p><h3 class="mb-0">{{v}}</h3>
        </div></div>
      </div>
      <div class="col-12">
        <div class="card glass shadow-sm"><div class="card-body">
          <div class="d-flex gap-2 mb-3">
            <button class="btn btn-primary" @click="reloadStats">Refresh Stats</button>
            <button class="btn btn-outline-primary" @click="loadCompanies">Companies</button>
            <button class="btn btn-outline-primary" @click="loadStudents">Students</button>
            <input v-model="state.searchQ" class="form-control" placeholder="Search companies/students/drives" />
            <button class="btn btn-dark" @click="search">Search</button>
          </div>
          <pre class="bg-light p-3 rounded">{{ state.adminData }}</pre>
        </div></div>
      </div>
    </div>
  `,
};
