import { RouteConfig } from 'vue-router';
import MainLayout from 'layouts/MainLayout.vue'

const routes: RouteConfig[] = [
  {
    path: '/',
    component: MainLayout,
    children: [
      { path: '',
        redirect: { path: 'fee/1'},
      },
      {
        name: 'fee:id',
        path: 'fee/:id',
        component: () => import('pages/Index.vue'),
      }
    ]
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '*',
    component: () => import('pages/Error404.vue')
  }
];

export default routes;
