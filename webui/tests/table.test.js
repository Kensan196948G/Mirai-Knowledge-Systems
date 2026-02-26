/**
 * TableManager Unit Tests
 * Mirai Knowledge Systems v1.5.0
 *
 * Jest unit tests for ui/table.js
 */

import { TableManager } from '../ui/table.js';

describe('TableManager', () => {
  describe('Basic Table Creation', () => {
    test('should create table with columns and data', () => {
      const columns = [
        { key: 'name', label: 'Name' },
        { key: 'age', label: 'Age' }
      ];
      const data = [
        { name: 'Alice', age: 30 },
        { name: 'Bob', age: 25 }
      ];

      const container = TableManager.create({ columns, data });

      expect(container).toBeInstanceOf(HTMLElement);
      expect(container.querySelector('table')).toBeTruthy();
      expect(container.querySelectorAll('tbody tr').length).toBe(2);
    });

    test('should create table headers correctly', () => {
      const columns = [
        { key: 'col1', label: 'Column 1' },
        { key: 'col2', label: 'Column 2' }
      ];

      const container = TableManager.create({ columns, data: [] });
      const headers = container.querySelectorAll('thead th');

      expect(headers.length).toBe(2);
      expect(headers[0].textContent).toBe('Column 1');
      expect(headers[1].textContent).toBe('Column 2');
    });

    test('should display "no data" message when data is empty', () => {
      const columns = [{ key: 'name', label: 'Name' }];
      const container = TableManager.create({ columns, data: [] });

      const noDataRow = container.querySelector('tbody tr.no-data');
      expect(noDataRow).toBeTruthy();
      expect(noDataRow.textContent).toContain('データがありません');
    });

    test('should apply custom className', () => {
      const columns = [{ key: 'name', label: 'Name' }];
      const container = TableManager.create({
        columns,
        data: [],
        className: 'custom-table'
      });

      expect(container.querySelector('table').classList.contains('custom-table')).toBe(true);
    });
  });

  describe('Column Configuration', () => {
    test('should support sortable columns', () => {
      const onSort = jest.fn();
      const columns = [
        { key: 'name', label: 'Name', sortable: true }
      ];

      const container = TableManager.create({
        columns,
        data: [],
        onSort
      });

      const th = container.querySelector('thead th');
      expect(th.classList.contains('sortable')).toBe(true);
      expect(th.style.cursor).toBe('pointer');

      th.click();
      expect(onSort).toHaveBeenCalledWith('name');
    });

    test('should set column width when specified', () => {
      const columns = [
        { key: 'name', label: 'Name', width: '200px' }
      ];

      const container = TableManager.create({ columns, data: [] });
      const th = container.querySelector('thead th');

      expect(th.style.width).toBe('200px');
    });

    test('should support custom render function', () => {
      const columns = [
        {
          key: 'price',
          label: 'Price',
          render: (value) => `¥${value.toLocaleString()}`
        }
      ];
      const data = [{ price: 1000 }];

      const container = TableManager.create({ columns, data });
      const td = container.querySelector('tbody td');

      expect(td.textContent).toBe('¥1,000');
    });

    test('should support render function returning HTMLElement', () => {
      const columns = [
        {
          key: 'status',
          label: 'Status',
          render: (value) => {
            const span = document.createElement('span');
            span.className = 'status-badge';
            span.textContent = value;
            return span;
          }
        }
      ];
      const data = [{ status: 'Active' }];

      const container = TableManager.create({ columns, data });
      const badge = container.querySelector('.status-badge');

      expect(badge).toBeTruthy();
      expect(badge.textContent).toBe('Active');
    });
  });

  describe('Row Interaction', () => {
    test('should call onRowClick when row is clicked', () => {
      const onRowClick = jest.fn();
      const columns = [{ key: 'name', label: 'Name' }];
      const data = [{ name: 'Alice' }];

      const container = TableManager.create({
        columns,
        data,
        onRowClick
      });

      const row = container.querySelector('tbody tr');
      row.click();

      expect(onRowClick).toHaveBeenCalledWith({ name: 'Alice' }, 0);
    });

    test('should add clickable-row class when onRowClick is provided', () => {
      const columns = [{ key: 'name', label: 'Name' }];
      const data = [{ name: 'Alice' }];

      const container = TableManager.create({
        columns,
        data,
        onRowClick: jest.fn()
      });

      const row = container.querySelector('tbody tr');
      expect(row.classList.contains('clickable-row')).toBe(true);
      expect(row.style.cursor).toBe('pointer');
    });
  });

  describe('Pagination', () => {
    test('should create pagination controls', () => {
      const pagination = {
        currentPage: 1,
        totalPages: 5,
        pageSize: 10,
        totalItems: 50,
        onPageChange: jest.fn()
      };

      const container = TableManager.create({
        columns: [{ key: 'name', label: 'Name' }],
        data: [],
        pagination
      });

      const paginationNav = container.querySelector('.pagination-container');
      expect(paginationNav).toBeTruthy();
    });

    test('should display current page and total pages', () => {
      const pagination = {
        currentPage: 2,
        totalPages: 5,
        onPageChange: jest.fn()
      };

      const container = TableManager.create({
        columns: [{ key: 'name', label: 'Name' }],
        data: [],
        pagination
      });

      const pageInfo = container.querySelector('.pagination-info');
      expect(pageInfo.textContent).toContain('ページ 2 / 5');
    });

    test('should disable previous button on first page', () => {
      const pagination = {
        currentPage: 1,
        totalPages: 5,
        onPageChange: jest.fn()
      };

      const container = TableManager.create({
        columns: [{ key: 'name', label: 'Name' }],
        data: [],
        pagination
      });

      const prevBtn = container.querySelector('.prev-btn');
      expect(prevBtn.disabled).toBe(true);
    });

    test('should disable next button on last page', () => {
      const pagination = {
        currentPage: 5,
        totalPages: 5,
        onPageChange: jest.fn()
      };

      const container = TableManager.create({
        columns: [{ key: 'name', label: 'Name' }],
        data: [],
        pagination
      });

      const nextBtn = container.querySelector('.next-btn');
      expect(nextBtn.disabled).toBe(true);
    });

    test('should call onPageChange when navigation buttons are clicked', () => {
      const onPageChange = jest.fn();
      const pagination = {
        currentPage: 2,
        totalPages: 5,
        onPageChange
      };

      const container = TableManager.create({
        columns: [{ key: 'name', label: 'Name' }],
        data: [],
        pagination
      });

      const prevBtn = container.querySelector('.prev-btn');
      const nextBtn = container.querySelector('.next-btn');

      prevBtn.click();
      expect(onPageChange).toHaveBeenCalledWith(1);

      nextBtn.click();
      expect(onPageChange).toHaveBeenCalledWith(3);
    });

    test('should display total items count when provided', () => {
      const pagination = {
        currentPage: 1,
        totalPages: 5,
        totalItems: 47,
        onPageChange: jest.fn()
      };

      const container = TableManager.create({
        columns: [{ key: 'name', label: 'Name' }],
        data: [],
        pagination
      });

      const itemsInfo = container.querySelector('.items-info');
      expect(itemsInfo.textContent).toContain('全 47 件');
    });
  });

  describe('Page Size Selector', () => {
    test('should create page size selector when onPageSizeChange is provided', () => {
      const pagination = {
        currentPage: 1,
        totalPages: 5,
        pageSize: 20,
        onPageChange: jest.fn(),
        onPageSizeChange: jest.fn()
      };

      const container = TableManager.create({
        columns: [{ key: 'name', label: 'Name' }],
        data: [],
        pagination
      });

      const selector = container.querySelector('.page-size-select');
      expect(selector).toBeTruthy();
    });

    test('should call onPageSizeChange when size is changed', () => {
      const onPageSizeChange = jest.fn();
      const pagination = {
        currentPage: 1,
        totalPages: 5,
        pageSize: 10,
        onPageChange: jest.fn(),
        onPageSizeChange
      };

      const container = TableManager.create({
        columns: [{ key: 'name', label: 'Name' }],
        data: [],
        pagination
      });

      const selector = container.querySelector('.page-size-select');
      selector.value = '50';
      selector.dispatchEvent(new Event('change'));

      expect(onPageSizeChange).toHaveBeenCalledWith(50);
    });
  });

  describe('Table Update', () => {
    test('should update existing table container', () => {
      const container = document.createElement('div');
      const columns = [{ key: 'name', label: 'Name' }];
      const data = [{ name: 'Alice' }];

      TableManager.update(container, { columns, data });

      expect(container.querySelector('table')).toBeTruthy();
      expect(container.querySelectorAll('tbody tr').length).toBe(1);
    });

    test('should handle null container gracefully', () => {
      expect(() => {
        TableManager.update(null, {
          columns: [{ key: 'name', label: 'Name' }],
          data: []
        });
      }).not.toThrow();
    });
  });

  describe('Sort Indicator', () => {
    test('should update sort indicator for ascending order', () => {
      const columns = [
        { key: 'name', label: 'Name', sortable: true }
      ];
      const container = TableManager.create({
        columns,
        data: [],
        onSort: jest.fn()
      });

      TableManager.updateSortIndicator(container, 'name', 'asc');

      const sortIcon = container.querySelector('[data-sort-key="name"]');
      expect(sortIcon.textContent).toContain('▲');
      expect(sortIcon.classList.contains('asc')).toBe(true);
    });

    test('should update sort indicator for descending order', () => {
      const columns = [
        { key: 'name', label: 'Name', sortable: true }
      ];
      const container = TableManager.create({
        columns,
        data: [],
        onSort: jest.fn()
      });

      TableManager.updateSortIndicator(container, 'name', 'desc');

      const sortIcon = container.querySelector('[data-sort-key="name"]');
      expect(sortIcon.textContent).toContain('▼');
      expect(sortIcon.classList.contains('desc')).toBe(true);
    });

    test('should handle null container gracefully', () => {
      expect(() => {
        TableManager.updateSortIndicator(null, 'name', 'asc');
      }).not.toThrow();
    });
  });

  describe('Data Rendering', () => {
    test('should handle null and undefined values', () => {
      const columns = [
        { key: 'name', label: 'Name' },
        { key: 'age', label: 'Age' }
      ];
      const data = [
        { name: 'Alice', age: null },
        { name: null, age: 25 }
      ];

      const container = TableManager.create({ columns, data });
      const cells = container.querySelectorAll('tbody td');

      expect(cells[1].textContent).toBe('');
      expect(cells[2].textContent).toBe('');
    });

    test('should convert values to strings', () => {
      const columns = [{ key: 'count', label: 'Count' }];
      const data = [{ count: 42 }];

      const container = TableManager.create({ columns, data });
      const cell = container.querySelector('tbody td');

      expect(cell.textContent).toBe('42');
    });
  });
});

describe('Global TableManager', () => {
  test('should be available on window object', () => {
    expect(window.TableManager).toBeDefined();
  });
});
