<template>
  <div style="padding: 20px;">
    <v-data-table :headers="headers" :items="products" item-key="code" :server-items-length="count" v-model="selected"
                  show-select @pagination="pageChange">
      <template v-slot:top>
        <v-list-item class="d-flex flex-wrap align-baseline">
          <v-text-field outlined dense label="产品型号" v-model="query.code"></v-text-field>
          &nbsp;&nbsp;
          <v-text-field outlined dense label="产品描述" v-model="query.desc"></v-text-field>
          &nbsp;&nbsp;
          <v-btn color="primary" @click="search">搜索</v-btn>
          &nbsp;&nbsp;
          <v-btn color="primary" @click="resetSearch">重置搜索</v-btn>
          &nbsp;&nbsp;
          <v-btn color="error" @click="showDelPopup">批量删除</v-btn>
          &nbsp;&nbsp;
          <v-btn color="success" @click="excelUploadDialog=true">Excel上传</v-btn>
        </v-list-item>
      </template>
      <template v-slot:item.actions="{item}">
        <v-btn x-small color="primary" @click="showEditPopup(item)">编辑</v-btn>
      </template>
    </v-data-table>
    <v-dialog v-model="editDialog" max-width="350">
      <v-card>
        <v-card-title>编辑</v-card-title>
        <v-card-text>
          <v-form ref="productEditForm" lazy-validation>
            <v-list-item>
              <v-text-field outlined dense label="产品型号" readonly v-model="editItem.code"></v-text-field>
            </v-list-item>
            <v-list-item>
              <v-text-field outlined dense label="抢购上限(0值表示不设上限)" type="number" v-model="editItem.wantLimit"
                            :rules="[v => !!v || '必填', v => parseInt(v) >=0 || '数值要求大于等于0']"></v-text-field>
            </v-list-item>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="editDialog=false">取消</v-btn>
          <v-btn color="success" @click="saveEdit">保存</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog v-model="delDialog" max-width="350">
      <v-card>
        <v-card-title>批量删除</v-card-title>
        <v-card-text style="text-align: left">
          <div v-for="(item, index) in selected" :key="index">
            {{ item.code }}
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="delDialog=false">取消</v-btn>
          <v-btn color="error" @click="saveDel">确认删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    <v-dialog v-model="excelUploadDialog" max-width="350">
      <v-card>
        <v-card-title>Excel上传</v-card-title>
        <v-card-text>
          <v-btn small block color="primary"
                 :href="$store.state.baseURL + '/tidcs/products/xlsx/template'">下载模版
          </v-btn>
          <v-form ref="excelUploadForm" lazy-validation>
            <v-list-item>
              <v-file-input label="选择文件" clearable v-model="uploadFile"
                            :rules="[v => !!v||'必填']"></v-file-input>
            </v-list-item>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="excelUploadDialog=false">取消</v-btn>
          <v-btn color="success" @click="excelUpload">确认上传</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import {request} from "../plugins/http";

export default {
  name: "TiProducts",
  computed: {
    headers() {
      return [
        {text: "产品型号", value: "code", sortable: false},
        {text: "抢购上限", value: "wantLimit", sortable: false},
        {text: "库存", value: "inventory", sortable: false},
        {text: "更新时间", value: "updateTime", sortable: false},
        {text: "产品描述", value: "desc", sortable: false},
        {text: "产品单价", value: "price", sortable: false},
        {text: "下单上限", value: "orderLimit", sortable: false},
        {text: "操作", value: "actions", sortable: false},
      ]
    }
  },
  data() {
    return {
      clock: null,
      query: {
        page: 1,
        limit: 10,
        code: "",
        desc: "",
      },
      products: [],
      count: 0,
      delDialog: false,
      selected: [],
      editDialog: false,
      editItem: {
        code: "",
        wantLimit: null,
      },
      excelUploadDialog: false,
      uploadFile: null,

    }
  },
  methods: {
    getProducts() {
      request(
        {method: "GET", url: "/tidcs/products", params: this.query},
        (res) => {
          this.products = res.data.data;
          this.count = res.data.count
        }
      )
    },
    pageChange(option) {
      if (this.page !== option.page || this.limit !== option.itemsPerPage) {
        this.query.page = option.page
        this.query.limit = option.itemsPerPage > 0 ? option.itemsPerPage : 0
        this.getProducts()
      }
    },
    search() {
      this.query.page = 1
      this.query.limit = 10
      this.getProducts()
    },
    resetSearch() {
      this.query.page = 1
      this.query.limit = 10
      this.query.code = ""
      this.query.desc = ""
      this.getProducts()
    },
    showDelPopup() {
      if (this.selected.length === 0) {
        this.$store.commit('setErrmsg', "请先勾选数据")
        return false
      }
      this.delDialog = true
    },
    saveDel() {
      let codes = this.selected.map((item) => {
        return item.code
      })
      request(
        {method: "DELETE", url: "/tidcs/products", data: {codes}},
        () => {
          this.getProducts()
          this.$store.commit("setErrmsg", "操作成功")
          this.delDialog = false
          this.selected = []
        }
      )
    },

    showEditPopup(item) {
      this.editItem = item
      this.editDialog = true
    },
    saveEdit() {
      if (!this.$refs.productEditForm.validate()) {
        return false
      }
      request(
        {method: "PUT", url: "/tidcs/products", data: {code: this.editItem.code, wantLimit: this.editItem.wantLimit}},
        () => {
          this.editItem = {}
          this.editDialog = false
          this.$store.commit('setErrmsg', "操作成功")
        }
      )
    },
    excelUpload() {
      if (!this.$refs.excelUploadForm.validate()) {
        return false
      }
      let formData = new FormData()
      formData.append("file", this.uploadFile)
      request(
        {method: "POST", url: "/tidcs/products", data: formData},
        () => {
          this.$store.commit('setErrmsg', '操作成功')
          this.$nextTick(() => {
            this.$refs.excelUploadForm.reset()
          })
          this.excelUploadDialog = false
          this.getProducts()
        }
      )

    },

  },
  activated() {
    this.getProducts()
    if (this.clock) {
      clearInterval(this.clock)
    }
    this.clock = setInterval(this.getProducts, 1000 * 60)
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
