<template>
  <div class="q-pa-md">
    <q-table
      title="Patent Documents"
      class="my-sticky-header-table"
      :data="data"
      :columns="columns"
      row-key="id"
      :pagination.sync="pagination"
      :loading="loading"
      :filter="filter"
      :rows-per-page-options="[50, 100, 500, 1000, 2500, 5000, 10000, 0]"
      @request="onRequest"
      binary-state-sort
    >

      <template v-slot:top-right>
        <div class="q-ml-xl">
          <q-btn
            color="primary"
            icon-right="archive"
            label="Export to csv"
            no-caps
            @click="exportTable"
          />
        </div>
        <div class="q-ml-xl">
          <q-input dense debounce="300" v-model="filter" placeholder="Search">
            <template v-slot:append>
              <q-icon name="search"></q-icon>
            </template>
          </q-input>
        </div>
        <div class="q-ml-xl">
          <q-btn
            flat round dense
            @click="toggle"
            :icon="$q.fullscreen.isActive ? 'fullscreen_exit' : 'fullscreen'"
            :label="$q.fullscreen.isActive ? 'Exit Fullscreen' : 'Go Fullscreen'"
            class="q-ml-md"
          />
        </div>
      </template>

      <template v-slot:header="props">
        <q-tr :props="props">
          <q-th auto-width>
            Fee History
          </q-th>
          <q-th
            v-for="col in props.cols"
            :key="col.name"
            :props="props"
          >
            {{ col.label }}
          </q-th>
        </q-tr>
      </template>

      <template v-slot:body="props">
        <q-tr :props="props">
          <q-td auto-width>
            <q-btn size="sm" color="primary" round dense @click="props.expand = !props.expand; hiya(props.row.patent_number)" :icon="props.expand ? 'remove' : 'add'" />
          </q-td>
          <q-td
            v-for="col in props.cols"
            :key="col.name"
            :props="props"
          >
            {{ col.value }}
          </q-td>
        </q-tr>
        <q-tr v-show="props.expand" :props="props">
          <q-td colspan="100%">
            <div class="text-left">This is expand slot for row above: {{ props.row.patent_number }}-{{ $route.params.id }}.</div>
          </q-td>
        </q-tr>
      </template>

    </q-table>
  </div>
</template>

<script>
import { axiosInstance } from 'boot/axios'
import {
  exportFile
} from 'quasar'

function wrapCsvValue(val, formatFn) {
  let formatted = formatFn !== void 0 ?
    formatFn(val) :
    val

  formatted = formatted === void 0 || formatted === null ?
    '' :
    String(formatted)

  formatted = formatted.split('"').join('""')
    /**
     * Excel accepts \n and \r in strings, but some other CSV parsers do not
     * Uncomment the next two lines to escape new lines
     */
    // .split('\n').join('\\n')
    // .split('\r').join('\\r')

  return `"${formatted}"`
}

export default {
  name: 'PageIndex',
  data() {
    return {
      // expanded: [466959,1855697,5418335],
      filter: '',
      loading: false,
      pagination: {
        sortBy: 'patent_number',
        descending: false,
        page: 1,
        rowsPerPage: 50,
        rowsNumber: 100
      },
      columns: [{
          name: 'patent_number',
          required: true,
          label: 'Patent Number',
          align: 'left',
          field: row => row.patent_number,
          sortable: true
        }, {
          name: 'issue_date',
          align: 'left',
          label: 'Issue Date',
          field: 'issue_date',
          sortable: true
        }, {
          name: 'application_number',
          align: 'left',
          label: 'Application Number',
          field: 'application_number',
          sortable: true
        }, {
          name: 'application_date',
          align: 'left',
          label: 'Application Date',
          field: 'application_date',
          sortable: true
        }, {
          name: 'pat_assignee_name',
          align: 'left',
          label: 'Assignee',
          field: 'pat_assignee_name',
          sortable: true
        }, {
          name: 'pat_assignee_address',
          align: 'left',
          label: 'Assignee Address',
          field: 'pat_assignee_address',
          sortable: false
        }, {
          name: 'correspondent_name',
          align: 'left',
          label: 'Correspondent',
          field: 'correspondent_name',
          sortable: true
        }, {
          name: 'correspondent_address',
          align: 'left',
          label: 'Correspondent Address',
          field: 'correspondent_address',
          sortable: false
        }, {
          name: 'entity_status',
          align: 'center',
          label: 'Entity Status',
          field: 'entity_status',
          sortable: false
        }
        // process link from frame number and reel number later
        // { name: 'link', label: 'Link', field: 'link', sortable: false },
      ],
      data: [],
      original: []
    }
  },
  mounted() {
    // this.loading = true
    this.onRequest({
        pagination: this.pagination,
        filter: undefined
      })
      // this.loading = false
  },
  methods: {
    onRequest(props) {
      const {
        page,
        rowsPerPage,
        sortBy,
        descending
      } = props.pagination
      console.log(props.pagination);
      const filter = props.filter

      this.loading = true

      // emulate server
      // update rowsCount with appropriate value
      // this.pagination.rowsNumber = this.getRowsNumberCount(filter)

      // get all rows if "All" (0) is selected
      const fetchCount = rowsPerPage === 0 ? this.pagination.rowsNumber : rowsPerPage

      // calculate starting row of data
      const startRow = (page - 1) * rowsPerPage
        // const endRow = startRow+fetchCount
        // fetch data from "server"
      const returnedData = this.fetchFromServer(startRow, fetchCount, filter, sortBy, descending)


      // clear out existing data and add new
      this.data.splice(0, this.data.length, ...returnedData)

      // don't forget to update local pagination object
      this.pagination.page = page
      this.pagination.rowsPerPage = rowsPerPage
      this.pagination.sortBy = sortBy
      this.pagination.descending = descending

      // ...and turn of loading indicator
      // this.loading = false
    },

    // emulate ajax call
    // SELECT * FROM ... WHERE...LIMIT...
    fetchFromServer(startRow, count, filter, sortBy, descending) {
      // this.loading = true
      console.log(startRow)
      console.log(count)
      console.log(filter)
      console.log(sortBy)
      console.log(descending)
      axiosInstance.request({
          method: 'GET',
          url: 'api/update_patents',
          params: {
            start_row: startRow,
            count: count,
            filter: filter,
            sort_by: sortBy,
            descending: descending
          }
        })
        .then(response => {
          console.log(response.data.patents)
          console.log(response.data.count)
          this.original = response.data.patents
          this.data = response.data.patents
          this.pagination.rowsNumber = response.data.count
          this.loading = false
        })
        .catch(e => {
          console.log(e)
        })

      const data = filter ?
        this.original.filter(row => row.patent_number.includes(filter)) :
        this.original.slice()

      // // handle sortBy
      // if (sortBy) {
      //   const sortFn = sortBy === 'patent_number'
      //     ? (descending
      //       ? (a, b) => (parseFloat(a.patent_number) > parseFloat(b.patent_number) ? -1 : parseFloat(a.patent_number) < parseFloat(b.patent_number) ? 1 : 0)
      //       : (a, b) => (parseFloat(a.patent_number) > parseFloat(b.patent_number) ? 1 : parseFloat(a.patent_number) < parseFloat(b.patent_number) ? -1 : 0)
      //     )
      //     : (descending
      //       ? (a, b) => (parseFloat(b[sortBy]) - parseFloat(a[sortBy]))
      //       : (a, b) => (parseFloat(a[sortBy]) - parseFloat(b[sortBy]))
      //     )
      //   data.sort(sortFn)
      // }

      return data.slice(startRow, startRow + count)
    },

    toggle(e) {
      const target = e.target.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode.parentNode
      this.$q.fullscreen.toggle(target)
        .then(() => {
          // success!
        })
        .catch((err) => {
          // alert(err)
          // uh, oh, error!!
          console.error(err)
        })
    },

    hiya(patent_number) {
      console.log('hiya friend: ' + String(patent_number))
    },

    exportTable() {
      // naive encoding to csv format
      const content = [this.columns.map(col => wrapCsvValue(col.label))].concat(
        this.data.map(row => this.columns.map(col => wrapCsvValue(
          typeof col.field === 'function' ?
          col.field(row) :
          row[col.field === void 0 ? col.name : col.field],
          col.format
        )).join(','))
      ).join('\r\n')

      const status = exportFile(
        'table-export.csv',
        content,
        'text/csv'
      )

      if (status !== true) {
        this.$q.notify({
          message: 'Browser denied file download...',
          color: 'negative',
          icon: 'warning'
        })
      }
    }
  }
}
</script>
