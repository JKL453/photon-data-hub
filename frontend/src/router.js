import { createRouter, createWebHistory } from "vue-router"

const EmptyRoute = { render: () => null }

const routes = [
  {
    path: "/",
    redirect: "/datasets",
  },
  {
    path: "/datasets",
    name: "datasets",
    component: EmptyRoute,
  },
  {
    path: "/datasets/:datasetId",
    name: "dataset-detail",
    component: EmptyRoute,
  },
  {
    path: "/datasets/:datasetId/files/:fileId",
    name: "file-detail",
    component: EmptyRoute,
  },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
