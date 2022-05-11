<template>
  <div>
    <div style="display: inline-block;height: 200px;line-height: 200px;font-size: 30px">
      <h1>TiDCS</h1>
    </div>
    <div class="d-flex justify-center align-center">
      <v-card width="348">
        <v-card-title>用户登录</v-card-title>
        <v-form ref="loginForm" lazy-validation>
          <v-list-item>
            <v-text-field label="账号" ref="account" v-model="account"
                          :rules="[v => !!v || '请输入账号']"></v-text-field>
          </v-list-item>
          <v-list-item>
            <v-text-field label="密码" ref="pwd" type="password" v-model="password"
                          :rules="[v => !!v || '请输入密码']"></v-text-field>
          </v-list-item>
          <v-list-item>
            <v-btn block color="success" @click="login">立即登录</v-btn>
          </v-list-item>
        </v-form>
      </v-card>
    </div>
  </div>

</template>

<script>
import {request} from '@/plugins/http';

export default {
  name: "Login",
  data() {
    return {
      account: "",
      password: "",
    }
  },
  methods: {
    login() {
      if (!this.$refs.loginForm.validate()) {
        return false
      }
      request(
        {
          method: "POST",
          url: "/tidcs/login",
          data: {
            account: this.account,
            password: this.password,
          }
        },
        (res) => {
          this.$store.commit("setUser", res.data.data)
          this.$router.push("/")
        })
    }
  }
}

</script>

<style scoped>

</style>
