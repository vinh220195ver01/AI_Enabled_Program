# Requirements: kiro-demo

Viết theo mẫu EARS. Mỗi yêu cầu có ID để truy vết sang test case.
Mục "Câu hỏi mở" cuối file là các điểm code hiện tại chưa rõ nghiệp vụ, cần người quyết định.

## 1. Tính giá đơn hàng (`pricing.py`)

### 1.1 Giảm giá theo số lượng

- **REQ-P01**: WHEN số lượng nhỏ hơn 10, THE system SHALL áp dụng mức giảm 0%.
- **REQ-P02**: WHEN số lượng từ 10 đến 49, THE system SHALL giảm 5% trên tổng tiền hàng.
- **REQ-P03**: WHEN số lượng từ 50 đến 99, THE system SHALL giảm 10% trên tổng tiền hàng.
- **REQ-P04**: WHEN số lượng từ 100 trở lên, THE system SHALL giảm 15% trên tổng tiền hàng.
- **REQ-P05**: IF số lượng nhỏ hơn 0, THEN THE system SHALL từ chối yêu cầu và báo lỗi "quantity must be >= 0".

### 1.2 Coupon

- **REQ-P06**: WHERE đơn hàng có mã coupon `SAVE10`, THE system SHALL giảm thêm 10% trên giá đã giảm theo số lượng.
- **REQ-P07**: WHERE đơn hàng có mã coupon `VIP20`, THE system SHALL giảm thêm 20% trên giá đã giảm theo số lượng.
- **REQ-P08**: THE system SHALL nhận mã coupon không phân biệt hoa thường.
- **REQ-P09**: WHERE đơn hàng không có mã coupon, THE system SHALL không áp dụng giảm giá coupon.
- **REQ-P10**: IF mã coupon không nằm trong danh sách hợp lệ, THEN THE system SHALL từ chối yêu cầu và báo lỗi "invalid coupon".
- **REQ-P11**: THE system SHALL áp giảm theo số lượng trước, sau đó mới áp coupon.

### 1.3 Phí vận chuyển

- **REQ-P12**: WHEN giá trị đơn sau tất cả giảm giá từ 500.000 trở lên, THE system SHALL đặt phí ship bằng 0.
- **REQ-P13**: WHEN giá trị đơn sau tất cả giảm giá nhỏ hơn 500.000, THE system SHALL cộng phí ship 30.000.

### 1.4 Kết quả và dữ liệu đầu vào

- **REQ-P14**: THE system SHALL trả về `subtotal`, `after_discount`, `shipping` và `total`, mỗi giá trị làm tròn 2 chữ số thập phân.
- **REQ-P15**: THE system SHALL tính `total` bằng `after_discount` cộng `shipping`.
- **REQ-P16**: IF đơn giá nhỏ hơn hoặc bằng 0, THEN THE system SHALL từ chối yêu cầu và báo lỗi "unit_price must be > 0".

## 2. Kiểm tra chất lượng dữ liệu (`check_orders.py`)

- **REQ-D01**: WHEN kiểm tra một dòng đơn hàng, THE system SHALL báo lỗi cho mỗi cột bắt buộc bị trống trong: `order_id`, `customer_id`, `unit_price`, `quantity`, `order_date`, `status`.
- **REQ-D02**: IF `order_id` đã xuất hiện ở dòng trước, THEN THE system SHALL báo lỗi trùng `order_id`.
- **REQ-D03**: IF `unit_price` không phải số, THEN THE system SHALL báo lỗi "unit_price is not a number".
- **REQ-D04**: IF `unit_price` nhỏ hơn hoặc bằng 0, THEN THE system SHALL báo lỗi "unit_price must be > 0".
- **REQ-D05**: IF `quantity` không phải số nguyên, THEN THE system SHALL báo lỗi "quantity is not an integer".
- **REQ-D06**: IF `quantity` nhỏ hơn hoặc bằng 0, THEN THE system SHALL báo lỗi "quantity must be > 0".
- **REQ-D07**: IF `order_date` không đúng định dạng `YYYY-MM-DD` hoặc không phải ngày có thật, THEN THE system SHALL báo lỗi "order_date must be YYYY-MM-DD".
- **REQ-D08**: IF `status` không thuộc `NEW`, `PAID`, `SHIPPED`, `CANCELLED`, THEN THE system SHALL báo lỗi "invalid status".
- **REQ-D09**: THE system SHALL ghi số dòng (tính cả dòng header là dòng 1) vào mỗi thông báo lỗi.
- **REQ-D10**: WHEN toàn bộ dữ liệu hợp lệ, THE system SHALL trả về danh sách lỗi rỗng và chương trình in "OK".

## 3. Câu hỏi mở (cần chốt trước khi viết test)

1. **Số lượng bằng 0**: code hiện chấp nhận `quantity = 0` và vẫn cộng phí ship 30.000 (tổng 30.000 cho đơn rỗng). Đây có phải hành vi đúng, hay phải từ chối như bên `check_orders.py` (REQ-D06)?
2. **Ngưỡng miễn phí ship**: tính trên giá *sau* giảm (như code) hay *trước* giảm?
3. **Cộng dồn giảm giá**: giảm theo số lượng và coupon nhân tuần tự (như code) hay cộng phần trăm?
4. **Coupon rỗng**: chuỗi rỗng `""` hiện bị coi là coupon không hợp lệ (báo lỗi), khác với `None`. Có đúng ý không?
5. **Kiểu số lượng**: `calculate_total` không kiểm tra `quantity` là số nguyên, còn phần kiểm tra dữ liệu thì có. Có cần thống nhất không?
6. **`customer_id`**: có cần kiểm tra tồn tại trong bảng khách hàng không (hiện chỉ kiểm tra không rỗng)?
7. **Ngày tương lai**: `order_date` ở tương lai có hợp lệ không?
