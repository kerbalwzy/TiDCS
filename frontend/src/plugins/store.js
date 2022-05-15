import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

const store = new Vuex.Store({
  state: {
    user: {
      account: "",
    },
    navs: [
      {
        path: "/",
        title: "在线插件",
      },
      // {
      //   path: "/products",
      //   title: "产品列表"
      // }
    ],
    baseURL: window.origin,
    // baseURL: "https://service-rixooyu8-1255484415.hk.apigw.tencentcs.com",
    errmsg: "",
  },
  mutations: {
    setErrmsg(state, msg) {
      state.errmsg = msg
      setTimeout(() => {
        state.errmsg = ""
      }, 5000)
    },
    setUser(state, user) {
      state.user = user
    },
    setNavs(state, navs) {
      state.navs = navs
    }
  },
  actions: {
    initAsync({commit}) { // 异步初始化

    },

  }
})

export default store
