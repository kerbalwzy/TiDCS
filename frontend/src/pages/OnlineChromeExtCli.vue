<template>
  <div style="padding: 20px">
    <v-data-table :headers="headers" :items="workers" item-key="sid" :items-per-page="workers.length"
                  hide-default-footer>
      <template v-slot:item.cart="{item}">
        <span v-if="!item.cart.CartId">未获取</span>
        <v-btn v-else small @click="showCart(item.cart)">{{ item.cart.CartTotal }}元</v-btn>
      </template>
      <template v-slot:item.Cookies="{item}">
        <span v-if="!item.cookies_str">未获取</span>
        <v-btn v-else small @click="showCookies(item)" color="primary">立即查看</v-btn>
      </template>
    </v-data-table>
    <v-dialog v-model="cartDialog" max-width="800px">
      <v-card>
        <v-card-title>购物车</v-card-title>
        <v-card-text>
          <v-list-item>
            <v-text-field dense outlined readonly label="产品种类" v-model="cart.CartCount"></v-text-field>
            &nbsp;&nbsp;
            <v-text-field dense outlined readonly label="产品总价( CNY )" v-model="cart.CartTotal"></v-text-field>
          </v-list-item>
          <v-data-table :headers="cartHeaders" :items="cart.Items" item-key="OpnId" :items-per-page="cart.Items.length"
                        hide-default-footer>
          </v-data-table>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="cartDialog=false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog v-model="cookieDialog">
      <v-card>
        <v-card-title>Ti-Cookies</v-card-title>
        <v-list-item>
          <v-textarea outlined dense label="Cookie字符串" v-model="cookies_str" readonly></v-textarea>
        </v-list-item>
        <v-list-item>
          <v-data-table :headers="cookiesHeaders" :items="cookies" :items-per-page="cookies.length" hide-default-footer>
            <template v-slot:item.expirationDate="{item}">
              <span v-if="item.expirationDate">{{ new Date(item.expirationDate*1000).toLocaleString() }}</span>
              <span v-else>Session</span>
            </template>
          </v-data-table>
        </v-list-item>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import {request} from "../plugins/http";

export default {
  name: "OnlineChromeExtCli",
  computed: {
    headers() {
      return [
        {text: "SID", value: "sid", sortable: false},
        {text: "登录邮箱", value: "email", sortable: false},
        {text: "公司名称", value: "companyName", sortable: false},
        {text: "网络延迟(ms)", value: "netDelay", sortable: false},
        {text: "在线检测", value: "lastOnlineAt", sortable: false},
        {text: "购物车", value: "cart", sortable: false},
        {text: "Cookies", value: "Cookies", sortable: false},
      ]
    },
    cartHeaders() {
      return [
        {text: "产品型号", value: "OpnId", sortable: false},
        {text: "产品描述", value: "Description", sortable: false},
        {text: "加购数量", value: "Quantity", sortable: false},
        {text: "总金额(CNY)", value: "Price", sortable: false},
      ]
    },
    cookiesHeaders() {
      return [
        {text: "domain", value: "domain", sortable: false},
        {text: "expirationDate", value: "expirationDate", sortable: false},
        {text: "name", value: "name", sortable: false},
        {text: "value", value: "value", sortable: false},
      ]
    }
  },
  data() {
    return {
      cartDialog: false,
      cookieDialog: false,
      workers: [],
      cart: {
        CartCount: "0",
        CartId: "451e2be7-3652-44f9-bb10-aff7a908f670",
        CartTotal: 0,
        ConversionRate: 6.72052044,
        Items: [
          {
            Description: "",
            OpnId: "",
            Price: 0,
            Quantity: ""
          }
        ],
      },
      cookies: [],
      cookies_str: "",
      clock: null,
    }
  },
  methods: {
    getWorkers() {
      request(
        {method: "GET", url: "/tidcs/workers"},
        (res) => {
          this.workers = res.data.data
        },
      )
    },
    showCart(cart) {
      if (!cart.CartTotal) {
        return false
      }
      this.cart = cart
      this.cartDialog = true
    },
    showCookies(item) {
      if (!item.cookies_str) {
        return false
      }
      this.cookies = item.cookies
      this.cookies_str = item.cookies_str
      this.cookieDialog = true
    }
  },
  activated() {
    this.getWorkers()
    if (this.clock) {
      clearInterval(this.clock)
    }
    this.clock = setInterval(this.getWorkers, 1000 * 30)
  },
  deactivated() {
    if (this.clock) {
      clearInterval(this.clock)
    }
  }

}
</script>

<style scoped>

</style>
