import axios from 'axios'
import router from '@/plugins/router'
import store from "./store";

axios.defaults.withCredentials = true

export function request(config, success, failure) {
  const instance = axios.create({
    baseURL: store.state.baseURL,
    // baseURL: window.origin,
    // timeout: 5000,
    withCredentials: true
  })
  instance(config).then((res) => {
    if (res.data.errcode === 0) {
      success(res)
    } else {
      store.commit('setErrmsg', res.data.msg)
    }
  }).catch((err) => {
    if (err.response.status === 403 && err.response.data.errcode === 40301) {
      router.push("/login")
    } else {
      failure ? failure(err) : null
    }
  })
}
