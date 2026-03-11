export const LoginRegisterPanel = {
  props: ['state', 'onLogin', 'onRegisterStudent', 'onRegisterCompany', 'onInitDb'],
  template: `
    <div>
      <div class="hero p-4 mb-4 shadow-sm">
        <h2 class="mb-1">Placement Portal Application</h2>
        <p class="mb-0">Admin, companies and students on one platform with complete placement lifecycle.</p>
      </div>
      <div class="row g-3">
        <div class="col-lg-4">
          <div class="card glass shadow-sm"><div class="card-body">
            <h5>Login</h5>
            <input v-model="state.login.email" class="form-control mb-2" placeholder="Email" />
            <input v-model="state.login.password" type="password" class="form-control mb-3" placeholder="Password" />
            <button class="btn btn-primary w-100" @click="onLogin">Login</button>
            <button class="btn btn-outline-secondary w-100 mt-2" @click="onInitDb">Initialize Database</button>
            <p class="small-muted mt-2 mb-0">Default admin: admin@ppa.local / admin123</p>
          </div></div>
        </div>
        <div class="col-lg-4">
          <div class="card glass shadow-sm"><div class="card-body">
            <h5>Student Registration</h5>
            <input v-model="state.student.email" class="form-control mb-2" placeholder="Email" />
            <input v-model="state.student.password" type="password" class="form-control mb-2" placeholder="Password" />
            <input v-model="state.student.full_name" class="form-control mb-2" placeholder="Full name" />
            <input v-model="state.student.branch" class="form-control mb-2" placeholder="Branch" />
            <div class="row g-2 mb-3">
              <div class="col"><input v-model="state.student.cgpa" class="form-control" placeholder="CGPA" /></div>
              <div class="col"><input v-model="state.student.year" class="form-control" placeholder="Year" /></div>
            </div>
            <button class="btn btn-success w-100" @click="onRegisterStudent">Register Student</button>
          </div></div>
        </div>
        <div class="col-lg-4">
          <div class="card glass shadow-sm"><div class="card-body">
            <h5>Company Registration</h5>
            <input v-model="state.company.email" class="form-control mb-2" placeholder="Email" />
            <input v-model="state.company.password" type="password" class="form-control mb-2" placeholder="Password" />
            <input v-model="state.company.company_name" class="form-control mb-2" placeholder="Company name" />
            <input v-model="state.company.hr_contact" class="form-control mb-2" placeholder="HR contact" />
            <input v-model="state.company.website" class="form-control mb-3" placeholder="Website" />
            <button class="btn btn-warning w-100" @click="onRegisterCompany">Register Company</button>
          </div></div>
        </div>
      </div>
    </div>
  `,
};
