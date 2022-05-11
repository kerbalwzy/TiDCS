import Vue from 'vue'
import Router from 'vue-router'
import Login from '../pages/Login'
import OnlineChromeExtCli from "../pages/OnlineChromeExtCli";
import TiProducts from "../pages/TiProducts";

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      name: 'OnlineChromeExtCli',
      component: OnlineChromeExtCli
    },
    {
      path: '/login',
      name: "Login",
      component: Login
    },
    {
      path: "/products",
      name: "TiProducts",
      component: TiProducts
    }]
})
