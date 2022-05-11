<template>
  <div id="app">
    <v-app>
      <v-navigation-drawer v-model="drawer" app v-if="navs.length > 0" width="200">
        <v-app-bar dark>
          <v-toolbar-title>TiDCS</v-toolbar-title>
        </v-app-bar>
        <v-list rounded>
          <v-list-item-group color="primary">
            <v-list-item v-for="(item, index) in navs" :key="index" :to="item.path">
              <v-list-item-title>{{ item.title }}</v-list-item-title>
            </v-list-item>
          </v-list-item-group>
        </v-list>
      </v-navigation-drawer>
      <v-app-bar app dark>
        <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>
        <v-btn icon @click="back">
          <v-icon>mdi-arrow-left</v-icon>
        </v-btn>
        <v-btn icon @click="flush">
          <v-icon>mdi-reload</v-icon>
        </v-btn>
        <v-snackbar v-model="snackbar" color="deep-purple accent-4" absolute>
          {{ errmsg }}
          <template v-slot:action="{ attrs }">
            <v-btn color="pink" text v-bind="attrs" @click="closeErrTip">Close</v-btn>
          </template>
        </v-snackbar>
        <v-spacer></v-spacer>
        <v-avatar color="indigo">
          <v-icon dark>mdi-account-circle</v-icon>
        </v-avatar>
        &nbsp;&nbsp;
        <v-toolbar-title>{{ user.account }}</v-toolbar-title>
        <v-btn v-if="user.account" depressed small @click="signOut">注销</v-btn>
      </v-app-bar>
      <v-main style="padding-top: 0">
        <keep-alive>
          <router-view></router-view>
        </keep-alive>
      </v-main>
    </v-app>
  </div>
</template>

<script>
import {request} from '@/plugins/http';

export default {
  name: 'App',
  computed: {
    user() {
      return this.$store.state.user
    },
    errmsg() {
      return this.$store.state.errmsg
    },
    role() {
      return this.$store.state.role
    },
    navs() {
      return this.$store.state.navs
    }
  },
  watch: {
    errmsg() {
      this.snackbar = this.$store.state.errmsg !== "";
    },
  },
  data() {
    return {
      drawer: null,
      snackbar: false,
    }
  },
  methods: {
    userProfile() {
      request(
        {method: "GET", url: "/tidcs/profile"},
        (res) => {
          this.$store.commit('setUser', res.data.data)
        }
      )
    },
    signOut() {
      request(
        {method: "GET", url: "/tidcs/logout"},
        () => {
          this.$store.commit("setUser", {account: ""})
          if (this.$route.name !== "Login") {
            this.$router.push("/login")
          }
        },
        () => {
        }
      )
    },
    flush() {
      this.$router.go(0)
    },
    back() {
      this.$router.back()
    },
    closeErrTip() {
      this.$store.commit("setErrmsg", "")
      this.snackbar = false
    }
  },
  mounted() {
    this.userProfile()
  },
}
</script>

<style>
#app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>
