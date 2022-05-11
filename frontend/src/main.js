// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'

import App from './App'
import router from '@/plugins/router'
import vuetify from '@/plugins/vuetify'
import store from '@/plugins/store'

Vue.config.productionTip = false
Array.prototype.insert = function (index) {
  index = Math.min(index, this.length);
  arguments.length > 1
  && this.splice.apply(this, [index, 0].concat([].pop.call(arguments)))
  && this.insert.apply(this, arguments);
  return this;
};
/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  vuetify,
  store,
  components: {App},
  template: '<App/>'
})

