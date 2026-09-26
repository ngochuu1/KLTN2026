2.4.2. Đặc tả Use case
2.4.2.1. Đăng ký tài khoản
Bảng 2.42. Đặc tả Use case Đăng ký tài khoản
[UC01]	Đăng ký tài khoản
Actor	Khách
Description	Use Case này cho phép Actor tạo tài khoản mới để sử dụng các chức năng của nền tảng học tập cộng tác trực tuyến.
Pre-Conditions	Actor chưa đăng nhập vào hệ thống.
Post-Conditions	Tài khoản mới được tạo thành công và thông tin tài khoản được lưu vào hệ thống.
 
 
 
Main Flow	1. Actor chọn chức năng “Đăng ký”.
2. Hệ thống hiển thị giao diện đăng ký tài khoản.
3. Actor nhập các thông tin đăng ký gồm họ tên, email, mật khẩu và xác nhận mật khẩu.
4. Actor chọn nút “Đăng ký”.
5. Hệ thống kiểm tra tính hợp lệ của thông tin được nhập.
6. Hệ thống kiểm tra email chưa được sử dụng bởi tài khoản khác. 
7. Hệ thống tạo tài khoản mới và lưu thông tin tài khoản. 
8. Hệ thống thông báo đăng ký thành công và điều hướng Actor đến giao diện đăng nhập.
Alternative Flow	Không có.
 Exception Flow	E1: Thông tin đăng ký không hợp lệ
- Tại bước 5, nếu thông tin không đúng định dạng hoặc thiếu trường bắt buộc, hệ thống hiển thị thông báo tương ứng. 
- Hệ thống giữ nguyên giao diện đăng ký để Actor chỉnh sửa thông tin. 
E2: Mật khẩu xác nhận không khớp
- Tại bước 5, nếu mật khẩu và xác nhận mật khẩu không giống nhau, hệ thống hiển thị thông báo lỗi. 
Actor nhập lại thông tin. 
E3: Email đã tồn tại
- Tại bước 6, nếu email đã được sử dụng, hệ thống thông báo email đã tồn tại. 
- Hệ thống không tạo tài khoản mới. 
2.4.2.2. Đăng nhập
Bảng 2.43. Đặc tả Use case Đăng nhập
[UC02]	Đăng nhập
Actor	Khách
Description	Use Case này cho phép Actor xác thực tài khoản và truy cập vào hệ thống.
Pre-Conditions	Actor đã có tài khoản hợp lệ và chưa đăng nhập vào hệ thống.
Post-Conditions	Actor đăng nhập thành công và được chuyển đến giao diện chính của hệ thống.
 
 
 
Main Flow	1. Actor truy cập giao diện đăng nhập. 
2. Hệ thống hiển thị biểu mẫu đăng nhập. 
3. Actor nhập email và mật khẩu. 
4. Actor chọn nút “Đăng nhập”. 
5. Hệ thống kiểm tra thông tin đăng nhập. 
6. Hệ thống xác thực tài khoản thành công. 
7. Hệ thống tạo phiên xác thực cho Actor. 
8. Hệ thống điều hướng Actor đến giao diện chính.
Alternative Flow	Không có.
 Exception Flow	E1: Thiếu thông tin đăng nhập
- Tại bước 4, nếu Actor chưa nhập email hoặc mật khẩu, hệ thống yêu cầu nhập đầy đủ thông tin. 
E2: Sai email hoặc mật khẩu
- Tại bước 5, nếu thông tin xác thực không chính xác, hệ thống thông báo “Email hoặc mật khẩu không chính xác”. 
- Actor có thể nhập lại thông tin. 
E3: Tài khoản bị khóa
- Tại bước 6, nếu tài khoản đang bị khóa, hệ thống từ chối đăng nhập và thông báo trạng thái tài khoản.

2.4.2.3. Đăng xuất
Bảng 2.44. Đặc tả use case Đăng xuất
[UC03]	Đăng xuất
Actor	Người dùng
Description	Use Case này cho phép Actor kết thúc phiên đăng nhập hiện tại và rời khỏi hệ thống.
Pre-Conditions	Actor đã đăng nhập vào hệ thống.
Post-Conditions	Phiên xác thực hiện tại của Actor được kết thúc và hệ thống chuyển về giao diện đăng nhập.
 Main Flow	1. Actor mở menu tài khoản cá nhân. 
2. Actor chọn chức năng “Đăng xuất”. 
3. Hệ thống thực hiện kết thúc phiên xác thực hiện tại. 
4. Hệ thống xóa thông tin xác thực tương ứng ở phía người dùng. 
5. Hệ thống điều hướng Actor đến giao diện đăng nhập.

Alternative Flow	Không có.
Exception Flow	Không có.
2.4.2.4. Xem và cập nhật thông tin cá nhân
Bảng 2.45. Đặc tả use case Xem và cập nhật thông tin cá nhân
[UC04]	Xem và cập nhật thông tin cá nhân
Actor	Người dùng
Description	Use Case này cho phép Actor xem và cập nhật các thông tin cá nhân của tài khoản.
Pre-Conditions	Actor đã đăng nhập vào hệ thống.
Post-Conditions	Thông tin cá nhân được cập nhật và lưu thành công nếu Actor thực hiện chỉnh sửa.
 
 
 
Main Flow	1. Actor chọn chức năng “Thông tin cá nhân”. 
2. Hệ thống truy xuất thông tin cá nhân của Actor. 
3. Hệ thống hiển thị thông tin cá nhân. 
4. Actor chọn chức năng chỉnh sửa. 
5. Actor thay đổi các thông tin được phép cập nhật. 
6. Actor chọn “Lưu thay đổi”. 
7. Hệ thống kiểm tra tính hợp lệ của dữ liệu. 
8. Hệ thống cập nhật thông tin. 
9. Hệ thống thông báo cập nhật thành công.
Alternative Flow	A1: Chỉ xem thông tin cá nhân
- Tại bước 4, Actor không chọn chỉnh sửa. 
- Use Case kết thúc và không có dữ liệu nào bị thay đổi. 
A2: Hủy cập nhật
- Tại bước 6, Actor chọn hủy. 
- Hệ thống không lưu các thay đổi và hiển thị lại thông tin trước khi chỉnh sửa.
Exception Flow	E1: Dữ liệu cập nhật không hợp lệ
- Tại bước 7, hệ thống phát hiện dữ liệu không hợp lệ. 
- Hệ thống hiển thị thông báo tại trường tương ứng và yêu cầu Actor chỉnh sửa.

2.4.2.5. Đổi mật khẩu
Bảng 2.46. Đặc tả use case Đổi mật khẩu
[UC05]	Đổi mật khẩu
Actor	Người dùng
Description	Use Case này cho phép Actor thay đổi mật khẩu của tài khoản đang sử dụng.
Pre-Conditions	Actor đã đăng nhập vào hệ thống.
Post-Conditions	Mật khẩu mới được cập nhật thành công.
 
 
 
Main Flow	1. Actor truy cập phần cài đặt tài khoản. 
2. Actor chọn “Đổi mật khẩu”. 
3. Hệ thống hiển thị giao diện đổi mật khẩu. 
4. Actor nhập mật khẩu hiện tại, mật khẩu mới và xác nhận mật khẩu mới. 
5. Actor chọn “Xác nhận”. 
6. Hệ thống xác thực mật khẩu hiện tại. 
7. Hệ thống kiểm tra tính hợp lệ của mật khẩu mới. 
8. Hệ thống cập nhật mật khẩu mới. 
9. Hệ thống thông báo đổi mật khẩu thành công.
Alternative Flow	Không có.
Exception Flow	E1: Mật khẩu hiện tại không chính xác
- Tại bước 6, hệ thống thông báo mật khẩu hiện tại không chính xác. 
- Mật khẩu không được thay đổi. 
E2: Mật khẩu mới không hợp lệ
- Tại bước 7, hệ thống thông báo yêu cầu về mật khẩu. 
- Actor nhập lại mật khẩu mới. 
E3: Xác nhận mật khẩu không khớp
- Hệ thống thông báo mật khẩu xác nhận không khớp. 
- Actor nhập lại thông tin.

2.4.2.6. Tạo Workspace
Bảng 2.47. Đặc tả use case Tạo Workspace
[UC06]	Tạo Workspace
Actor	Người dùng
Description	Use Case này cho phép Actor tạo một Workspace mới làm không gian học tập cộng tác cho một nhóm người dùng.
Pre-Conditions	Actor đã đăng nhập vào hệ thống.
Post-Conditions	Workspace mới được tạo và Actor trở thành Chủ Workspace.
 
 
 
Main Flow	1. Actor chọn chức năng “Tạo Workspace”. 
2. Hệ thống hiển thị giao diện tạo Workspace. 
3. Actor nhập tên Workspace, mô tả và các thông tin cần thiết. 
4. Actor chọn “Tạo Workspace”. 
5. Hệ thống kiểm tra tính hợp lệ của thông tin. 
6. Hệ thống tạo Workspace mới. 
7. Hệ thống gán Actor làm Chủ Workspace (OWNER). 
8. Hệ thống khởi tạo các thông tin mặc định cần thiết cho Workspace. 
9. Hệ thống chuyển Actor vào Workspace vừa tạo.
Alternative Flow	A1: Hủy tạo Workspace
- Actor chọn “Hủy” trước khi xác nhận tạo. 
- Hệ thống đóng giao diện tạo Workspace và không lưu dữ liệu.
Exception Flow	E1: Thông tin Workspace không hợp lệ
- Tại bước 5, hệ thống hiển thị thông báo đối với trường dữ liệu không hợp lệ. 
- Actor chỉnh sửa và thực hiện lại.


2.4.2.7. Xem danh sách Workspace
Bảng 2.48. Đặc tả use case Xem danh sách Workspace
[UC07]	Xem danh sách Workspace
Actor	Người dùng
Description	Use Case này cho phép Actor xem danh sách các Workspace mà mình đang tham gia hoặc sở hữu.
Pre-Conditions	Actor đã đăng nhập vào hệ thống.
Post-Conditions	Danh sách Workspace của Actor được hiển thị.
 
 
 
Main Flow	1. Actor truy cập khu vực Workspace. 
2. Hệ thống xác định tài khoản của Actor. 
3. Hệ thống truy xuất các Workspace mà Actor là thành viên. 
4. Hệ thống hiển thị danh sách Workspace. 
5. Actor có thể chọn một Workspace để truy cập. 
6. Hệ thống hiển thị Workspace được chọn theo quyền của Actor.
Alternative Flow	A1: Chưa tham gia Workspace nào
- Tại bước 4, nếu Actor chưa thuộc Workspace nào, hệ thống hiển thị trạng thái danh sách trống và cung cấp chức năng tạo/tham gia Workspace.
Exception Flow	Không có.

2.4.2.8. Mời thành viên vào Workspace
Bảng 2.49. Đặc tả use case Mời thành viên vào Workspace
[UC08]	Mời thành viên vào Workspace
Actor	Chủ Workspace / Người có quyền quản lý
Description	Use Case này cho phép Actor gửi lời mời để người dùng khác tham gia Workspace.
Pre-Conditions	Actor đã đăng nhập, đang thuộc Workspace và có quyền mời thành viên.
Post-Conditions	Một lời mời tham gia Workspace hợp lệ được tạo để người được mời có thể tham gia Workspace.
 
 
 
 
 
Main Flow	1. Actor truy cập Workspace. 
2. Actor mở chức năng quản lý/mời thành viên. 
3. Actor chọn “Mời thành viên”. 
4. Hệ thống hiển thị giao diện tạo lời mời. 
5. Actor nhập hoặc chọn thông tin người cần mời. 
6. Actor xác nhận gửi lời mời. 
7. Hệ thống kiểm tra quyền của Actor và thông tin người được mời. 
8. Hệ thống tạo lời mời tham gia Workspace. 
9. Hệ thống thông báo gửi lời mời thành công.
Alternative Flow	 A1: Mời bằng liên kết/mã mời
- Tại bước 5, Actor chọn tạo liên kết hoặc mã mời. 
- Hệ thống tạo thông tin mời tương ứng. 
- Actor có thể sao chép và gửi thông tin này cho người dùng khác. 
A2: Hủy mời
- Actor đóng giao diện trước khi xác nhận. 
- Hệ thống không tạo lời mời.
Exception Flow	E1: Người dùng đã là thành viên
- Tại bước 7, nếu người được mời đã thuộc Workspace, hệ thống thông báo người dùng đã là thành viên. 
E2: Actor không còn quyền mời thành viên
- Hệ thống từ chối thao tác và thông báo Actor không có quyền thực hiện.


2.4.2.9. Tham gia Workspace
Bảng 2.50. Đặc tả use case Tham gia Workspace
[UC09]	Tham gia Workspace
Actor	Người dùng
Description	Use Case này cho phép Actor tham gia một Workspace thông qua lời mời hoặc thông tin mời hợp lệ.
Pre-Conditions	Actor đã đăng nhập và chưa là thành viên của Workspace cần tham gia.
Post-Conditions	Actor trở thành thành viên của Workspace với quyền thành viên mặc định.
Main Flow	1. Actor mở lời mời tham gia Workspace. 
2. Hệ thống kiểm tra tính hợp lệ của lời mời. 
3. Hệ thống hiển thị thông tin cơ bản của Workspace. 
4. Actor chọn “Tham gia Workspace”. 
5. Hệ thống kiểm tra Actor chưa thuộc Workspace. 
6. Hệ thống thêm Actor vào danh sách thành viên với quyền mặc định MEMBER. 
7. Hệ thống cập nhật trạng thái lời mời nếu cần. 
8. Hệ thống thông báo tham gia thành công. 
9. Hệ thống điều hướng Actor đến Workspace.

Alternative Flow	A1: Tham gia bằng mã/liên kết mời
- Actor nhập mã hoặc truy cập liên kết mời. 
- Hệ thống xác định Workspace tương ứng. 
- Luồng tiếp tục từ bước 2. 
A2: Từ chối lời mời
- Tại bước 4, Actor chọn từ chối. 
- Hệ thống cập nhật trạng thái lời mời và không thêm Actor vào Workspace.
 Exception Flow	E1: Lời mời không hợp lệ hoặc hết hạn
- Tại bước 2, hệ thống thông báo lời mời không còn hiệu lực. 
- Actor không được thêm vào Workspace. 
E2: Actor đã là thành viên
- Tại bước 5, hệ thống thông báo Actor đã thuộc Workspace và không tạo bản ghi thành viên trùng lặp.
2.4.2.10. Cập nhật thông tin Workspace
Bảng 2.51. Đặc tả use case Cập nhật thông tin Workspace
[UC10]	Cập nhật thông tin Workspace
Actor	Chủ Workspace / Người có quyền quản lý
Description	Use Case này cho phép Actor chỉnh sửa các thông tin cơ bản của Workspace.
Pre-Conditions	Actor đã đăng nhập, thuộc Workspace và có quyền quản lý Workspace.
Post-Conditions	Thông tin Workspace được cập nhật và lưu thành công.
 
 
 
Main Flow	1. Actor truy cập Workspace cần quản lý. 
2. Actor mở phần “Cài đặt Workspace”. 
3. Hệ thống kiểm tra quyền quản lý của Actor. 
4. Hệ thống hiển thị thông tin hiện tại của Workspace. 
5. Actor chỉnh sửa các thông tin được phép thay đổi như tên, mô tả, ảnh đại diện hoặc các thiết lập liên quan. 
6. Actor chọn “Lưu thay đổi”. 
7. Hệ thống kiểm tra tính hợp lệ của dữ liệu. 
8. Hệ thống cập nhật thông tin Workspace. 
9. Hệ thống thông báo cập nhật thành công và hiển thị thông tin mới.
Alternative Flow	A1: Hủy cập nhật
- Tại bước 6, Actor chọn hủy. 
- Hệ thống không lưu các thay đổi.
Exception Flow	E1: Actor không có quyền
- Tại bước 3, nếu Actor không có quyền quản lý Workspace, hệ thống từ chối truy cập chức năng. 
E2: Thông tin cập nhật không hợp lệ
- Tại bước 7, hệ thống hiển thị thông báo tại trường dữ liệu không hợp lệ. 
- Actor chỉnh sửa và thực hiện lại.
2.4.2.11. Quản lý thành viên Workspace
Bảng 2.52. Đặc tả use case Quản lý thành viên Workspace
[UC11]	Quản lý thành viên Workspace
Actor	Chủ Workspace / Người có quyền quản lý
Description	Use Case này cho phép Actor tra cứu danh sách toàn bộ thành viên trong Workspace, lọc thành viên theo vai trò và thực hiện loại bỏ thành viên ra khỏi không gian học tập khi cần thiết.
Pre-Conditions	- Actor đã đăng nhập thành công vào hệ thống.
- Actor đang ở trong Workspace và có vai trò Chủ Workspace (OWNER) hoặc Quản lý (ADMIN).
Post-Conditions	- Danh sách thành viên được hiển thị trực quan kèm vai trò tương ứng.
- Thành viên bị loại bỏ sẽ không còn quyền truy cập vào Workspace và toàn bộ các kênh thuộc Workspace đó.
 
 
 
Main Flow	1. Actor truy cập vào Workspace cần quản lý.
2. Actor mở menu Workspace và chọn chức năng “Quản lý thành viên”.
3. Hệ thống kiểm tra quyền hạn của Actor.
4. Hệ thống truy xuất danh sách thành viên thuộc Workspace.
5. Hệ thống hiển thị danh sách thành viên cùng vai trò tương ứng (OWNER, ADMIN, MEMBER).
6. Actor tìm và chọn thành viên cần xử lý trong danh sách.
7. Actor chọn nút “Xóa khỏi Workspace”.
8. Hệ thống hiển thị hộp thoại yêu cầu xác nhận thao tác loại bỏ thành viên.
9. Actor xác nhận thao tác.
10. Hệ thống kiểm tra điều kiện xóa (đảm bảo không xóa tài khoản Chủ sở hữu).
11. Hệ thống loại thành viên khỏi danh sách thành viên của Workspace.
12. Hệ thống cập nhật lại danh sách hiển thị và gửi thông báo thao tác thành công.
Alternative Flow	A1: Chỉ xem danh sách thành viên
- Tại bước 6, Actor chỉ theo dõi thông tin hoặc tìm kiếm thành viên mà không chọn xóa.
- Use Case kết thúc và không có dữ liệu nào bị thay đổi.
A2: Hủy thao tác xóa thành viên
- Tại bước 9, Actor chọn "Hủy" hoặc đóng hộp thoại xác nhận.
- Hệ thống giữ nguyên trạng thái thành viên và không thực hiện thao tác xóa.
Exception Flow	E1: Actor không có quyền quản lý
- Tại bước 3, nếu quyền của Actor không đủ, hệ thống từ chối truy cập và hiển thị cảnh báo không có quyền thao tác.
E2: Không được loại Chủ Workspace
- Tại bước 10, nếu thành viên được chọn mang vai trò OWNER, hệ thống từ chối thực thi và thông báo: "Không thể loại bỏ Chủ sở hữu khỏi Workspace". 
E3: Thành viên không còn tồn tại trong Workspace
- Tại bước 10, nếu thành viên đã rời nhóm hoặc bị xóa trước đó, hệ thống thông báo dữ liệu đã thay đổi và tải lại danh sách mới nhất.

 
2.4.2.12. Phân quyền thành viên Workspace
Bảng 2.53. Đặc tả use case Phân quyền thành viên Workspace
[UC12]	Phân quyền thành viên Workspace
Actor	Chủ Workspace
Description	Use Case này cho phép Chủ Workspace thay đổi cấp độ phân quyền của thành viên (chuyển đổi qua lại giữa hai vai trò MEMBER và ADMIN) nhằm phân chia quyền quản lý không gian học tập.
Pre-Conditions	- Actor đã đăng nhập và là Chủ Workspace (OWNER).
- Thành viên cần phân quyền đang thuộc Workspace và không phải là chính Actor.
Post-Conditions	- Vai trò mới của thành viên được cập nhật thành công trong hệ thống.
- Quyền hạn tương ứng của thành viên được áp dụng ngay lập tức trong toàn bộ Workspace.
 
 
 
Main Flow	1. Actor truy cập vào khu vực “Quản lý thành viên” của Workspace.
2. Hệ thống hiển thị danh sách thành viên kèm vai trò hiện tại.
3. Actor chọn thành viên cần thay đổi quyền hạn.
4. Actor chọn chức năng “Thay đổi vai trò”.
5. Hệ thống hiển thị danh sách các vai trò được phép gán (ADMIN, MEMBER).
6. Actor chọn vai trò mới muốn thiết lập.
7. Actor nhấn xác nhận thay đổi.
8. Hệ thống kiểm tra quyền OWNER của Actor và tính hợp lệ của vai trò mới.
9. Hệ thống cập nhật vai trò mới của thành viên vào cơ sở dữ liệu.
10. Hệ thống cập nhật giao diện hiển thị và thông báo cập nhật vai trò thành công.
Alternative Flow	A1: Hủy phân quyền
- Tại bước 7, Actor chọn hủy bỏ trước khi xác nhận.
- Hệ thống đóng menu lựa chọn và giữ nguyên vai trò hiện tại của thành viên.
 Exception Flow	E1: Actor không phải Chủ Workspace
- Tại bước 8, nếu Actor không mang vai trò OWNER, hệ thống từ chối thao tác và thông báo quyền hạn không đủ.
E2: Thay đổi vai trò không hợp lệ
- Tại bước 8, nếu Actor cố tình gán vai trò không hợp lệ hoặc tự phân quyền cho chính mình, hệ thống hiển thị thông báo lỗi và giữ nguyên dữ liệu cũ.
2.4.2.13. Rời Workspace
Bảng 2.54. Đặc tả use case Rời Workspace
[UC13]	Rời Workspace
Actor	Thành viên Workspace
Description	Use Case này cho phép người dùng chủ động rời khỏi một Workspace khi không còn nhu cầu tham gia học tập hoặc trao đổi môn học.
Pre-Conditions	- Actor đã đăng nhập thành công vào hệ thống.
- Actor hiện đang là thành viên hợp lệ của Workspace cần rời.
Post-Conditions	- Actor không còn là thành viên của Workspace.
- Quyền truy cập vào Workspace bị thu hồi và Workspace bị loại khỏi danh sách hiển thị của Actor.
 
 
 
Main Flow	1. Actor truy cập vào Workspace muốn rời khỏi.
2. Actor mở menu tùy chọn của Workspace.
3. Actor chọn chức năng “Rời Workspace”.
4. Hệ thống hiển thị hộp thoại xác nhận: "Bạn có chắc chắn muốn rời khỏi không gian học tập này?".
5. Actor nhấn nút xác nhận rời Workspace.
6. Hệ thống kiểm tra vai trò hiện tại của Actor trong Workspace.
7. Hệ thống xóa tư cách thành viên của Actor khỏi Workspace.
8. Hệ thống thông báo rời Workspace thành công.
9. Hệ thống điều hướng Actor ra giao diện danh sách Workspace còn lại.

Alternative Flow	A1: Hủy rời Workspace
- Tại bước 5, Actor chọn nút "Hủy" hoặc đóng hộp thoại xác nhận.
- Hệ thống đóng hộp thoại và không thay đổi dữ liệu thành viên.
 Exception Flow	E1: Chủ Workspace thực hiện rời Workspace
- Tại bước 6, nếu Actor đang giữ vai trò OWNER, hệ thống từ chối yêu cầu và hiển thị cảnh báo: "Chủ sở hữu không thể rời Workspace. Vui lòng xóa Workspace hoặc chuyển quyền sở hữu trước khi rời".

2.4.2.14. Xóa Workspace
Bảng 2.55. Đặc tả use case Xóa Workspace
[UC14]	Xóa Workspace
Actor	Chủ Workspace
Description	Use Case này cho phép Chủ sở hữu gỡ bỏ hoàn toàn một Workspace khỏi hệ thống khi không gian học tập không còn hoạt động.
Pre-Conditions	- Actor đã đăng nhập thành công vào hệ thống.
- Actor là người sáng lập và nắm giữ quyền Chủ sở hữu (OWNER) của Workspace.
Post-Conditions	- Workspace không còn khả dụng đối với toàn bộ thành viên.
- Dữ liệu Workspace được cập nhật trạng thái xóa theo chính sách lưu trữ của hệ thống.
 
 
 
Main Flow	1. Actor truy cập phần cài đặt của Workspace cần xóa.
2. Actor chọn mục “Xóa Workspace”.
3. Hệ thống kiểm tra quyền OWNER của Actor đối với Workspace.
4. Hệ thống hiển thị cảnh báo nguy hiểm về việc toàn bộ dữ liệu kênh và trao đổi sẽ bị ngưng truy cập.
5. Hệ thống yêu cầu Actor nhập tên Workspace hoặc chọn nút xác nhận xóa.
6. Actor xác nhận thực hiện xóa.
7. Hệ thống tiến hành cập nhật trạng thái xóa Workspace trong cơ sở dữ liệu.
8. Hệ thống xử lý các dữ liệu liên quan thuộc Workspace theo chính sách hệ thống.
9. Hệ thống thông báo xóa Workspace thành công.
10. Hệ thống điều hướng Actor quay trở lại giao diện danh sách Workspace chính.
Alternative Flow	A1: Hủy thao tác xóa
- Tại bước 6, Actor chọn hủy thao tác hoặc đóng giao diện xác nhận.
- Hệ thống hủy bỏ tiến trình và giữ nguyên trạng thái hoạt động của Workspace.
 Exception Flow	E1: Actor không phải Chủ Workspace
- Tại bước 3, nếu Actor không phải là OWNER, hệ thống từ chối quyền truy cập chức năng và ghi nhận cảnh báo vi phạm quyền.
E2: Quá trình xử lý xóa gặp sự cố
- Tại bước 7, nếu xảy ra lỗi kết nối cơ sở dữ liệu, hệ thống giữ Workspace ở trạng thái an toàn và thông báo: "Thao tác xóa thất bại, vui lòng thử lại sau".

2.4.2.15. Tạo kênh
Bảng 2.56. Đặc tả use case Tạo kênh
[UC15]	Tạo kênh
Actor	Chủ Workspace / Người có quyền quản lý
Description	Use Case này cho phép Actor khởi tạo kênh trao đổi mới (kênh chat văn bản hoặc phòng tự học trực tuyến) trong Workspace để phân luồng nội dung thảo luận và học tập theo từng chủ đề.
Pre-Conditions	- Actor đã đăng nhập thành công vào hệ thống.
- Actor thuộc Workspace và có quyền quản lý kênh (OWNER hoặc ADMIN).
Post-Conditions	- Kênh mới được tạo thành công và liên kết trực thuộc Workspace tương ứng.
- Kênh mới được cập nhật trên danh sách kênh của toàn bộ thành viên trong Workspace.
 
 
 
Main Flow	1. Actor truy cập vào Workspace muốn thêm kênh.
2. Actor chọn chức năng “Tạo kênh” tại danh mục kênh.
3. Hệ thống kiểm tra quyền quản lý kênh của Actor.
4. Hệ thống hiển thị biểu mẫu tạo kênh mới.
5. Actor nhập tên kênh, chọn loại kênh (Kênh văn bản hoặc Phòng tự học) và điền phần mô tả.
6. Actor nhấn nút “Tạo”.
7. Hệ thống kiểm tra tính hợp lệ của dữ liệu nhập.
8. Hệ thống tạo kênh mới và lưu thông tin vào Workspace.
9. Hệ thống cập nhật danh sách kênh của Workspace.
10. Hệ thống thông báo tạo kênh thành công và điều hướng Actor vào kênh vừa tạo.
Alternative Flow	A1: Hủy tạo kênh
- Tại bước 5, Actor chọn "Hủy" hoặc đóng biểu mẫu tạo kênh.
- Hệ thống đóng giao diện và không lưu dữ liệu.
 Exception Flow	E1: Actor không có quyền tạo kênh
- Tại bước 3, nếu Actor mang vai trò MEMBER, hệ thống hiển thị thông báo không có quyền thực hiện thao tác.
E2: Thông tin kênh không hợp lệ
- Tại bước 7, nếu tên kênh bị bỏ trống hoặc trùng với kênh đã có trong Workspace, hệ thống hiển thị lỗi tại ô nhập và yêu cầu Actor điều chỉnh lại.

2.4.2.16. Cập nhật thông tin kênh
Bảng 2.57.Đặc tả use case Cập nhật thông tin kênh
[UC16]	Cập nhật thông tin kênh
Actor	Chủ Workspace / Người có quyền quản lý
Description	Use Case này cho phép Actor chỉnh sửa tên kênh, mô tả chuyên đề hoặc các thiết lập hoạt động nhằm phục vụ nhu cầu thay đổi của lớp học/nhóm học tập.
Pre-Conditions	Actor đã đăng nhập và có quyền quản lý kênh. Kênh tồn tại trong Workspace.
Post-Conditions	Thông tin kênh được cập nhật thành công.
 
 
 
Main Flow	1. Actor chọn kênh cần chỉnh sửa từ danh sách kênh.
2. Actor mở phần cài đặt của kênh.
3. Hệ thống kiểm tra quyền quản lý kênh của Actor.
4. Hệ thống hiển thị thông tin hiện tại của kênh.
5. Actor chỉnh sửa tên, mô tả hoặc các thiết lập được phép.
6. Actor chọn “Lưu thay đổi”.
7. Hệ thống kiểm tra tính hợp lệ của dữ liệu.
8. Hệ thống cập nhật thông tin kênh trong cơ sở dữ liệu.
9. Hệ thống thông báo cập nhật thành công và đóng cửa sổ cài đặt.
Alternative Flow	A1: Hủy cập nhật
- Actor chọn hủy thao tác. Hệ thống giữ nguyên thông tin ban đầu.
 Exception Flow	E1: Actor không có quyền
- Tại bước 3, hệ thống từ chối mở cài đặt nếu không đủ quyền.
E2: Tên kênh rỗng hoặc trùng lặp
- Tại bước 7, hệ thống hiển thị lỗi tại ô nhập và giữ nguyên giao diện để Actor chỉnh sửa.





2.4.2.17. Xóa kênh
Bảng 2.58. Đặc tả use case Xóa kênh
[UC17]	Xóa kênh
Actor	Chủ Workspace, Người có quyền quản lý
Description	Trường hợp sử dụng này cho phép Actor tìm kiếm các bài viết hoặc tài khoản của người dùng khác trên hệ thống dựa vào từ khóa.
Pre-Conditions	- Kênh cần xóa đang tồn tại trong Workspace.
- Actor có quyền quản lý kênh (OWNER hoặc ADMIN).
- Kênh được chọn không phải là kênh mặc định (#general) của Workspace.
Post-Conditions	- Kênh bị xóa khỏi cơ sở dữ liệu và không còn khả dụng đối với bất kỳ thành viên nào.
- Các thành viên đang ở trong kênh bị điều hướng về kênh mặc định.
 
 
 
Main Flow	1. Actor chọn kênh cần xóa.
2. Actor mở phần cài đặt kênh.
3. Actor chọn “Xóa kênh”.
4. Hệ thống kiểm tra quyền hạn và xác minh kênh không phải kênh mặc định.
5. Hệ thống hiển thị cảnh báo xác nhận xóa.
6. Actor xác nhận xóa.
7. Hệ thống thực hiện xóa kênh khỏi cơ sở dữ liệu.
8. Hệ thống loại bỏ kênh khỏi danh mục hiển thị của Workspace.
9. Hệ thống thông báo xóa thành công và chuyển Actor về kênh mặc định.
Alternative Flow	A1: Hủy xóa
- Tại bước 6, Actor không xác nhận. Kênh được giữ nguyên.
 Exception Flow	E1: Actor không có quyền
- Tại bước 4, hệ thống từ chối thao tác.
E2: Xóa kênh mặc định
- Tại bước 4, nếu Actor chọn xóa kênh mặc định của Workspace, hệ thống cảnh báo: "Không được phép xóa kênh mặc định" và khóa chức năng xóa.

2.4.2.18. Gửi tin nhắn trong kênh
Bảng 2.59. Đặc tả use case Gửi tin nhắn trong kênh
[UC18]	Gửi tin nhắn trong kênh
Actor	Thành viên Workspace
Description	Use Case này cho phép Actor soạn và gửi tin nhắn văn bản theo thời gian thực tới các thành viên khác trong cùng một kênh chat.
Pre-Conditions	- Actor là thành viên Workspace và đang mở kênh chat tương ứng.
Post-Conditions	- Tin nhắn được lưu vào cơ sở dữ liệu (chat_messages).
- Tin nhắn hiển thị tức thì trên giao diện của các thành viên đang trực tuyến trong kênh.
 
 
 
Main Flow	1. Actor truy cập một kênh trò chuyện.
2. Hệ thống tải lịch sử tin nhắn gần nhất của kênh.
3. Actor nhập nội dung tin nhắn vào ô soạn thảo.
4. Actor nhấn Enter hoặc chọn biểu tượng gửi.
5. Hệ thống kiểm tra quyền truy cập kênh và tính hợp lệ của nội dung tin nhắn.
6. Hệ thống lưu tin nhắn mới vào cơ sở dữ liệu.
7. Hệ thống gửi sự kiện tin nhắn mới (WebSocket) đến các thành viên đang kết nối với kênh.
8. Giao diện hiển thị tin nhắn mới và tự động cuộn xuống cuối danh sách.
Alternative Flow	Không có.
 Exception Flow	E1: Nội dung tin nhắn trống
- Tại bước 5, nếu nội dung chỉ chứa khoảng trắng, hệ thống không thực hiện gửi tin.
E2: Mất quyền truy cập
- Tại bước 5, nếu Actor đã bị loại khỏi Workspace, hệ thống từ chối gửi và thông báo không có quyền.
E3: Kết nối thời gian thực bị gián đoạn
- Tại bước 6, nếu đường truyền mạng gặp sự cố, hệ thống gắn cờ báo lỗi cạnh tin nhắn kèm tùy chọn gửi lại.

2.4.2.19. Chỉnh sửa/Xóa tin nhắn
Bảng 2.60. Đặc tả use case Chỉnh sửa/Xóa tin nhắn
[UC19]	Chỉnh sửa/Xóa tin nhắn
Actor	Thành viên Workspace
Description	Use Case này cho phép Actor chỉnh sửa lại nội dung hoặc xóa tin nhắn do chính mình đã gửi trong kênh chat.
Pre-Conditions	- Actor đang mở kênh chat.
- Tin nhắn cần thao tác do chính Actor gửi và chưa bị xóa trước đó.
Post-Conditions	- Nội dung tin nhắn được cập nhật kèm trạng thái “(đã chỉnh sửa)”, hoặc tin nhắn bị gỡ bỏ khỏi luồng trò chuyện của kênh.
 
 
 
Main Flow	1. Actor chọn tin nhắn do mình gửi từ danh sách.
2. Actor chọn chức năng “Chỉnh sửa”.
3. Hệ thống kiểm tra quyền sở hữu tin nhắn của Actor.
4. Hệ thống mở ô chỉnh sửa văn bản trực tiếp tại dòng tin nhắn.
5. Actor nhập nội dung mới.
6. Actor xác nhận lưu.
7. Hệ thống kiểm tra nội dung mới.
8. Hệ thống cập nhật nội dung tin nhắn và ghi nhận thời gian chỉnh sửa.
9. Hệ thống đồng bộ nội dung mới đến các thành viên đang kết nối.
10. Giao diện hiển thị trạng thái tin nhắn đã chỉnh sửa.
Alternative Flow	A1: Xóa tin nhắn
- Tại bước 2, Actor chọn “Xóa tin nhắn”.
- Hệ thống kiểm tra quyền sở hữu và yêu cầu xác nhận.
- Actor nhấn xác nhận.
- Hệ thống cập nhật trạng thái xóa tin và đồng bộ gỡ bỏ tin nhắn trên giao diện của các thành viên trong kênh.
A2: Hủy thao tác
- Tại bước 5, Actor nhấn phím Escape hoặc chọn hủy. Hệ thống giữ nguyên tin nhắn ban đầu.
 Exception Flow	E1: Actor không phải người gửi
- Tại bước 3, hệ thống từ chối thao tác nếu Actor không sở hữu tin nhắn.
E2: Tin nhắn không còn tồn tại
- Tại bước 3, nếu tin nhắn đã bị xóa trước đó, hệ thống làm mới danh sách tin.
E3: Nội dung chỉnh sửa để trống
- Tại bước 7, nếu Actor xóa hết chữ, hệ thống yêu cầu Actor nhập nội dung hoặc dùng chức năng xóa.

2.4.2.20. Gửi tệp trong kênh chat
Bảng 2.61. Đặc tả use case Gửi tệp trong kênh chat
[UC20]	Gửi tệp trong kênh chat
Actor	Thành viên Workspace
Description	Use Case này cho phép Actor đính kèm và gửi nhanh tệp tài liệu, ảnh minh họa trong kênh chat để phục vụ trao đổi tức thời.
Pre-Conditions	- Actor đang mở kênh chat văn bản.
- Tệp cần gửi có sẵn trên thiết bị của Actor.
Post-Conditions	- Tệp được lưu trữ trên hệ thống lưu trữ đối tượng (Object Storage).
- Tin nhắn chứa tệp đính kèm được tạo và hiển thị trong kênh để các thành viên tải về.

 
 
 
Main Flow	1. Actor truy cập kênh chat.
2. Actor chọn chức năng “Đính kèm tệp”.
3. Hệ thống mở giao diện chọn tệp trên thiết bị.
4. Actor chọn tệp cần gửi.
5. Hệ thống kiểm tra định dạng và kích thước tệp.
6. Actor xác nhận gửi.
7. Hệ thống tải tệp lên vùng lưu trữ.
8. Hệ thống tạo thông tin tệp đính kèm và tạo bản ghi tin nhắn mới.
9. Hệ thống lưu thông tin tin nhắn vào cơ sở dữ liệu.
10. Hệ thống gửi sự kiện tin nhắn mới đến các thành viên đang kết nối.
11. Tệp đính kèm được hiển thị trực tiếp trong khung chat.
Alternative Flow	A1: Gửi tệp kèm nội dung văn bản
- Actor nhập thêm chữ trước khi gửi. Hệ thống lưu đồng thời văn bản và thông tin tệp trong cùng một tin nhắn.
A2: Hủy chọn tệp
- Actor nhấn nút gỡ tệp xem trước trước khi gửi. Hệ thống không tải tệp lên máy chủ.
 Exception Flow	E1: Định dạng tệp không được hỗ trợ
- Tại bước 5, nếu tệp thuộc loại tệp bị chặn, hệ thống hiển thị cảnh báo và từ chối nhận tệp.
E2: Kích thước tệp vượt quá giới hạn
- Tại bước 5, nếu dung lượng tệp vượt quá 25MB, hệ thống từ chối tải lên và thông báo giới hạn dung lượng.
E3: Quá trình tải tệp thất bại
- Tại bước 7, nếu gặp lỗi đường truyền khi lưu tệp, hệ thống thông báo lỗi và yêu cầu Actor thử lại.
2.4.2.21. Thả cảm xúc cho tin nhắn
Bảng 2.62. Đặc tả use case Thả cảm xúc cho tin nhắn
[UC21]	Thả cảm xúc cho tin nhắn
Actor	Thành viên Workspace
Description	
Use Case này cho phép Actor thả biểu tượng cảm xúc vào các tin nhắn được gửi trong kênh chat nhằm phản hồi nhanh nội dung trao đổi của các thành viên khác.

Pre-Conditions	- Actor đã đăng nhập thành công vào hệ thống và là thành viên của Workspace.
- Actor đang truy cập kênh chat có chứa tin nhắn muốn tương tác.
Post-Conditions	- Biểu tượng cảm xúc được thêm vào hoặc loại bỏ khỏi tin nhắn theo thao tác của Actor.
- Thông tin cảm xúc mới của tin nhắn được cập nhật cho các thành viên đang hoạt động trong kênh.
 
 
 
Main Flow	1. Actor chọn Workspace và kênh chat muốn tham gia trao đổi.
2. Hệ thống hiển thị lịch sử các tin nhắn trong kênh.
3. Actor di chuyển đến tin nhắn muốn tương tác và nhấn chọn biểu tượng thêm cảm xúc.
4. Hệ thống hiển thị danh sách các biểu tượng cảm xúc có thể sử dụng.
5. Actor chọn một biểu tượng cảm xúc.
6. Hệ thống ghi nhận cảm xúc của Actor vào tin nhắn được chọn.
7. Hệ thống cập nhật biểu tượng, số lượng phản hồi và hiển thị thay đổi cho các thành viên trong kênh.
Alternative Flow	A1: Actor bỏ cảm xúc đã thả
- Tại bước 5, nếu Actor chọn lại biểu tượng cảm xúc mà mình đã thả trước đó, hệ thống xác định Actor đã có phản hồi tương ứng trên tin nhắn.
- Hệ thống xóa cảm xúc của Actor khỏi tin nhắn, giảm số lượng phản hồi của biểu tượng đó và cập nhật lại giao diện.
A2: Actor chọn cảm xúc khác
- Tại bước 5, Actor chọn thêm một biểu tượng cảm xúc khác với biểu tượng đã sử dụng trước đó.
- Hệ thống ghi nhận thêm phản hồi mới của Actor và cập nhật các biểu tượng đang hiển thị trên tin nhắn.
 Exception Flow	E1: Tin nhắn đã bị xóa
- Tại bước 6, nếu tin nhắn đã bị người gửi hoặc người có quyền quản lý xóa trước đó, hệ thống không thực hiện việc thêm cảm xúc.
- Hệ thống loại tin nhắn không còn tồn tại khỏi giao diện hiện tại và cập nhật lại danh sách tin nhắn cho Actor.
2.4.2.22. Tham gia phòng tự học
Bảng 2.63. Đặc tả use case Tham gia phòng tự học
[UC22]	Tham gia phòng tự học
Actor	Thành viên Workspace
Description	Use Case này mô tả cách Actor tham gia vào phòng tự học trực tuyến của kênh để học tập cùng các thành viên khác. Trước khi vào phòng, Actor có thể kiểm tra và thiết lập microphone, camera; sau khi tham gia có thể sử dụng các chức năng học tập trực tuyến và theo dõi phiên Pomodoro chung của phòng.
Pre-Conditions	- Actor đã đăng nhập thành công vào hệ thống và là thành viên của Workspace.
- Actor có quyền truy cập vào kênh chứa phòng tự học.
- Phòng tự học đang hoạt động và cho phép thành viên tham gia.
Post-Conditions	- Actor tham gia thành công vào phòng và được hiển thị trong danh sách thành viên đang trực tuyến.
- Thời điểm Actor bắt đầu tham gia phòng được ghi nhận làm thời điểm bắt đầu phiên tự học.
- Trạng thái hiện tại của phòng và phiên Pomodoro được đồng bộ cho Actor.
 
Main Flow	1. Actor chọn Workspace muốn tham gia từ danh sách Workspace của mình.
2. Actor chọn kênh có phòng tự học từ danh sách kênh của Workspace.
3. Actor nhấn chọn chức năng “Phòng tự học”.
4. Hệ thống kiểm tra quyền truy cập của Actor và hiển thị giao diện chuẩn bị trước khi vào phòng.
5. Hệ thống hiển thị trạng thái microphone, camera và hình ảnh xem trước của Actor.
6. Actor kiểm tra các thiết bị và thiết lập trạng thái microphone, camera theo nhu cầu.
7. Actor nhấn chọn nút “Tham gia phòng”.
8. Hệ thống tạo phiên tham gia phòng cho Actor và thiết lập kết nối với các thành viên đang có trong phòng.
9. Hệ thống ghi nhận thời điểm bắt đầu phiên tự học của Actor.
10. Hệ thống lấy trạng thái hiện tại của phòng, danh sách thành viên và thông tin phiên Pomodoro đang diễn ra nếu có.
11. Hệ thống hiển thị giao diện phòng tự học và đồng bộ sự xuất hiện của Actor đến các thành viên khác trong phòng.
Alternative Flow	A1: Actor tham gia với microphone tắt
- Tại bước 6, Actor nhấn tắt microphone trước khi tham gia phòng.
- Hệ thống lưu trạng thái thiết bị được lựa chọn và Actor tiếp tục thực hiện từ bước 7.
- Sau khi vào phòng, các thành viên khác nhìn thấy microphone của Actor ở trạng thái tắt.
A2: Actor tham gia với camera tắt
- Tại bước 6, Actor lựa chọn tắt camera trước khi tham gia.
- Hệ thống không truyền hình ảnh của Actor khi vào phòng nhưng vẫn cho phép Actor sử dụng các chức năng còn lại.
A3: Actor thay đổi thiết bị sử dụng
- Tại bước 6, nếu thiết bị có nhiều microphone hoặc camera, Actor chọn thiết bị khác từ danh sách thiết bị khả dụng.
- Hệ thống cập nhật thiết bị được lựa chọn và hiển thị lại trạng thái kiểm tra cho Actor trước khi tham gia.
Exception Flow	E1: Actor chưa cấp quyền sử dụng microphone/camera
- Tại bước 5, nếu trình duyệt chưa được cấp quyền truy cập microphone hoặc camera, hệ thống yêu cầu Actor cấp quyền sử dụng thiết bị.
- Nếu Actor đồng ý, hệ thống kiểm tra lại thiết bị và tiếp tục luồng tại bước 6.
- Nếu Actor từ chối, hệ thống đặt thiết bị tương ứng ở trạng thái tắt và Actor vẫn có thể tham gia phòng.
E2: Actor không còn quyền truy cập kênh
- Tại bước 4, nếu Actor đã bị loại khỏi Workspace hoặc không còn quyền truy cập kênh, hệ thống thông báo Actor không có quyền tham gia phòng và quay lại giao diện Workspace.
E3: Không thể kết nối vào phòng tự học
- Tại bước 8, nếu hệ thống không thể thiết lập phiên tham gia, hệ thống hiển thị thông báo kết nối thất bại.
- Actor vẫn ở giao diện chuẩn bị trước khi vào phòng và có thể nhấn “Tham gia phòng” để thực hiện lại yêu cầu.
2.4.2.23. Rời phòng tự học
Bảng 2.64.  Đặc tả use case Rời phòng tự học
[UC23]	Rời phòng tự học
Actor	Thành viên Workspace
Description	Use Case này mô tả cách Actor rời khỏi phòng tự học sau khi kết thúc quá trình học trực tuyến.
Pre-Conditions	Actor đang tham gia một phòng tự học và có phiên tự học đang được hệ thống ghi nhận.
Post-Conditions	- Actor được đưa ra khỏi phòng tự học và không còn xuất hiện trong danh sách thành viên trực tuyến của phòng.
- Các kết nối microphone, camera hoặc chia sẻ màn hình đang sử dụng được kết thúc.
- Phiên tự học của Actor được kết thúc, thời gian tham gia được ghi nhận để sử dụng cho chức năng thống kê học tập.
 
Main Flow	1. Tại giao diện phòng tự học, Actor nhấn chọn nút “Rời phòng”.
2. Hệ thống tiếp nhận yêu cầu rời phòng của Actor.
3. Hệ thống dừng các luồng microphone, camera và chia sẻ màn hình đang được Actor sử dụng.
4. Hệ thống ghi nhận thời điểm Actor rời phòng và kết thúc phiên tự học hiện tại.
5. Hệ thống tính thời lượng tham gia của Actor dựa trên thời điểm bắt đầu và kết thúc phiên học.
6. Hệ thống cập nhật Actor ra khỏi danh sách thành viên đang trực tuyến và gửi trạng thái mới đến những thành viên còn lại.
7. Hệ thống chuyển Actor từ giao diện phòng tự học trở về giao diện kênh.
Alternative Flow	A1: Actor rời phòng khi đang chia sẻ màn hình
- Tại bước 1, nếu Actor đang chia sẻ màn hình và nhấn “Rời phòng”, hệ thống tự động kết thúc luồng chia sẻ trước khi đóng phiên tham gia.
- Hệ thống tiếp tục thực hiện từ bước 4 của luồng chính.
A2: Actor tham gia lại sau khi đã rời phòng
- Sau khi hoàn thành bước 7, nếu phòng vẫn hoạt động, Actor có thể chọn lại chức năng tham gia phòng.
- Hệ thống thực hiện UC22 – Tham gia phòng tự học và tạo một phiên tham gia mới cho Actor.
Exception Flow	E1: Actor mất kết nối mà không chủ động rời phòng
- Nếu hệ thống phát hiện Actor bị mất kết nối, trạng thái của Actor được chuyển sang mất kết nối tạm thời.
- Nếu Actor kết nối lại trong khoảng thời gian cho phép, hệ thống khôi phục phiên tham gia hiện tại và không tạo phiên học mới.
- Nếu Actor không kết nối lại, hệ thống tự động kết thúc phiên, ghi nhận thời điểm kết nối hợp lệ cuối cùng và cập nhật Actor ra khỏi danh sách thành viên trong phòng.
E2: Không thể ghi nhận thời điểm kết thúc phiên
- Tại bước 4, nếu xảy ra lỗi khi cập nhật thông tin phiên tự học, hệ thống vẫn thực hiện việc đưa Actor ra khỏi phòng.
- Thông tin phiên được giữ ở trạng thái cần xử lý để tránh làm mất toàn bộ dữ liệu thời gian học đã được ghi nhận trước đó.
2.4.2.24. Bật/Tắt microphone
Bảng 2.65. Đặc tả use case Bật/Tắt microphone
[UC24]	Bật/Tắt microphone
Actor	Thành viên Workspace
Description	Use Case này cho phép Actor bật hoặc tắt microphone của mình trong phòng tự học để chủ động tham gia trao đổi bằng âm thanh với các thành viên khác.
Pre-Conditions	- Actor đang tham gia phòng tự học.
- Để bật microphone, thiết bị của Actor phải có microphone khả dụng và trình duyệt được cấp quyền truy cập thiết bị âm thanh.
Post-Conditions	Trạng thái microphone của Actor được cập nhật và hiển thị cho các thành viên trong phòng.
 
Main Flow	1. Actor nhấn chọn biểu tượng microphone trên thanh điều khiển của phòng tự học.
2. Hệ thống kiểm tra trạng thái hiện tại của microphone.
3. Hệ thống kiểm tra quyền truy cập thiết bị microphone của trình duyệt.
4. Hệ thống kích hoạt microphone và bắt đầu truyền âm thanh của Actor vào phòng.
5. Hệ thống thay đổi biểu tượng microphone trên giao diện sang trạng thái đang bật.
6. Hệ thống cập nhật trạng thái microphone mới của Actor đến các thành viên đang có trong phòng.
Alternative Flow	A1: Actor tắt microphone
- Tại bước 2, nếu microphone đang ở trạng thái bật, hệ thống không thực hiện bước 3 và bước 4.
- Hệ thống ngừng truyền âm thanh của Actor vào phòng và chuyển trạng thái microphone thành tắt.
- Hệ thống cập nhật biểu tượng microphone của Actor trên giao diện của các thành viên khác.
A2: Actor bật lại microphone sau khi tắt
- Actor nhấn lại biểu tượng microphone.
- Nếu quyền truy cập thiết bị vẫn còn hiệu lực, hệ thống kích hoạt lại microphone mà không yêu cầu Actor cấp quyền lần nữa và tiếp tục luồng tại bước 4.
Exception Flow	E1: Trình duyệt chưa được cấp quyền microphone
- Tại bước 3, hệ thống yêu cầu trình duyệt hiển thị hộp thoại xin quyền sử dụng microphone.
- Nếu Actor chọn cho phép, hệ thống tiếp tục thực hiện bước 4.
- Nếu Actor từ chối, hệ thống giữ microphone ở trạng thái tắt và hiển thị thông báo hướng dẫn Actor cấp lại quyền nếu muốn sử dụng chức năng.
E2: Không tìm thấy microphone khả dụng
- Tại bước 3, nếu hệ thống không phát hiện thiết bị microphone, hệ thống hiển thị thông báo không tìm thấy thiết bị âm thanh.
- Actor vẫn tiếp tục tham gia phòng nhưng không thể bật microphone.
E3: Microphone bị ngắt trong khi đang sử dụng
- Nếu thiết bị microphone bị ngắt kết nối sau bước 4, hệ thống dừng luồng âm thanh và chuyển trạng thái microphone của Actor thành tắt.
- Hệ thống thông báo cho Actor và cập nhật trạng thái mới đến các thành viên trong phòng.
2.4.2.25. Bật/Tắt camera
Bảng 2.66. Đặc tả use case Bật/Tắt camera
[UC25]	Bật/Tắt camera
Actor	Thành viên Workspace
Description	Use Case này cho phép thành viên chủ động bật hoặc tắt camera khi tham gia phòng tự học. Chức năng hỗ trợ các thành viên tương tác trực quan trong quá trình học nhóm, đồng thời cho phép mỗi thành viên tự quyết định trạng thái hình ảnh của mình trong phòng.
Pre-Conditions	- Actor đang tham gia phòng tự học.
- Khi Actor muốn bật camera, thiết bị phải có camera khả dụng.
Post-Conditions	- Camera của Actor được chuyển sang trạng thái tương ứng với thao tác vừa thực hiện.
- Khi camera được bật, hình ảnh của Actor được hiển thị trong phòng; khi camera được tắt, hệ thống ngừng truyền hình ảnh của Actor.
 
Main Flow	1. Actor nhấn chọn biểu tượng camera trên thanh điều khiển của phòng tự học.
2. Hệ thống kiểm tra trạng thái camera hiện tại của Actor.
3. Hệ thống kiểm tra quyền truy cập camera của trình duyệt.
4. Hệ thống kích hoạt camera được Actor lựa chọn.
5. Hệ thống hiển thị hình ảnh camera của Actor trên giao diện phòng tự học.
6. Hệ thống cập nhật trạng thái camera của Actor thành đang bật.
7. Hệ thống gửi trạng thái mới và hiển thị hình ảnh của Actor cho các thành viên khác trong phòng.
Alternative Flow	A1: Actor tắt camera
- Tại bước 2, nếu camera đang bật, hệ thống dừng việc truyền hình ảnh từ thiết bị của Actor.
- Hệ thống chuyển trạng thái camera thành tắt và thay thế khu vực hình ảnh bằng thông tin đại diện của Actor.
- Trạng thái camera mới được cập nhật đến các thành viên trong phòng.
A2: Actor thay đổi camera đang sử dụng
- Trong trường hợp thiết bị có nhiều camera, Actor mở phần cài đặt thiết bị và chọn camera khác.
- Hệ thống dừng luồng hình ảnh từ camera hiện tại, kích hoạt camera mới và cập nhật lại hình ảnh mà không yêu cầu Actor rời phòng.
Exception Flow	E1: Actor chưa cấp quyền truy cập camera
- Tại bước 3, trình duyệt yêu cầu Actor cấp quyền sử dụng camera.
- Nếu Actor đồng ý, hệ thống tiếp tục kích hoạt camera tại bước 4.
- Nếu Actor từ chối, hệ thống giữ camera ở trạng thái tắt và Actor vẫn có thể sử dụng microphone, Pomodoro và các chức năng khác của phòng.
E2: Không có camera khả dụng
- Nếu hệ thống không phát hiện camera trên thiết bị, chức năng bật camera không được thực hiện và hệ thống hiển thị thông báo cho Actor.
E3: Camera bị mất kết nối trong khi đang bật
- Hệ thống phát hiện luồng hình ảnh bị gián đoạn và dừng sử dụng camera.
- Hệ thống chuyển trạng thái camera của Actor thành tắt, cập nhật trạng thái đến các thành viên khác và thông báo lỗi cho Actor.
2.4.2.26. Chia sẻ màn hình
Bảng 2.67. Đặc tả use case Chia sẻ màn hình
[UC26]	Chia sẻ màn hình
Actor	Thành viên Workspace
Description	Use Case này cho phép Actor chia sẻ toàn bộ màn hình, một cửa sổ ứng dụng hoặc một tab trình duyệt cho các thành viên khác đang tham gia phòng tự học. Chức năng được sử dụng khi thành viên cần trình bày nội dung, cùng xem tài liệu hoặc trao đổi bài tập trong quá trình học nhóm.
Pre-Conditions	- Actor đang tham gia phòng tự học.
- Trình duyệt và thiết bị của Actor hỗ trợ chức năng chia sẻ màn hình.
Post-Conditions	- Nếu Actor bắt đầu chia sẻ thành công, nội dung được lựa chọn được hiển thị cho các thành viên khác trong phòng và trạng thái chia sẻ của Actor được cập nhật.
- Khi Actor dừng chia sẻ, luồng chia sẻ được kết thúc và trạng thái của Actor được đưa về không chia sẻ màn hình.
 
Main Flow	1. Actor nhấn chọn chức năng “Chia sẻ màn hình” trên thanh điều khiển của phòng tự học.
2. Hệ thống yêu cầu trình duyệt mở giao diện lựa chọn nội dung cần chia sẻ.
3. Trình duyệt hiển thị các nguồn có thể chia sẻ như toàn bộ màn hình, cửa sổ ứng dụng hoặc tab trình duyệt.
4. Actor lựa chọn nguồn nội dung muốn chia sẻ.
5. Actor xác nhận bắt đầu chia sẻ.
6. Hệ thống tiếp nhận luồng nội dung được Actor lựa chọn và thiết lập trạng thái chia sẻ màn hình.
7. Hệ thống hiển thị nội dung được chia sẻ cho các thành viên đang tham gia phòng.
8. Hệ thống cập nhật trạng thái Actor đang chia sẻ màn hình cho các thành viên khác.
9. Actor tiếp tục chia sẻ nội dung trong quá trình học tập.
10. Khi hoàn thành, Actor nhấn chọn “Dừng chia sẻ”.
11. Hệ thống kết thúc luồng chia sẻ, cập nhật lại trạng thái của Actor và ngừng hiển thị nội dung được chia sẻ trong phòng.
Alternative Flow	A1: Actor hủy lựa chọn nội dung chia sẻ
- Tại bước 4, Actor đóng giao diện lựa chọn hoặc chọn hủy mà không lựa chọn nguồn nội dung.
- Trình duyệt đóng giao diện lựa chọn và hệ thống không thiết lập luồng chia sẻ màn hình.
- Actor quay lại phòng tự học và tiếp tục sử dụng các chức năng khác như bình thường.
Exception Flow	E1: Trình duyệt hoặc thiết bị không hỗ trợ chia sẻ màn hình
- Tại bước 2, nếu môi trường hiện tại không hỗ trợ chức năng chia sẻ màn hình, hệ thống không thể mở giao diện lựa chọn nguồn.
- Hệ thống thông báo chức năng không khả dụng trên thiết bị hoặc trình duyệt hiện tại và Actor tiếp tục ở trong phòng tự học.
E2: Luồng chia sẻ bị gián đoạn
- Sau bước 6, nếu nguồn đang được chia sẻ bị đóng, quyền chia sẻ bị thu hồi hoặc luồng nội dung bị gián đoạn, hệ thống dừng việc hiển thị nội dung chia sẻ.
- Hệ thống cập nhật trạng thái của Actor thành không chia sẻ màn hình và thông báo cho Actor biết phiên chia sẻ đã kết thúc.
2.4.2.27. Quản lý phiên Pomodoro chung

Bảng 2.68. Đặc tả use case Quản lý phiên Pomodoro chung
[UC27]	Quản lý phiên Pomodoro chung
Actor	Chủ phòng / Thành viên có quyền
Description	Use Case này cho phép Actor thiết lập và điều khiển phiên Pomodoro chung của phòng tự học. Các thành viên trong phòng sử dụng cùng một bộ đếm thời gian để thực hiện các khoảng tập trung và nghỉ giải lao đồng bộ.
Pre-Conditions	- Actor đang tham gia phòng tự học.
- Actor được phép điều khiển Pomodoro chung của phòng.
Post-Conditions	Trạng thái hiện tại của phiên Pomodoro, bao gồm giai đoạn tập trung/nghỉ, thời điểm bắt đầu và trạng thái hoạt động, được hệ thống ghi nhận và đồng bộ cho các thành viên trong phòng. Các khoảng tập trung hoàn thành được sử dụng làm dữ liệu phục vụ ghi nhận hoạt động tự học.
 
Main Flow	1. Actor chọn chức năng “Pomodoro” trong phòng tự học.
2. Hệ thống hiển thị trạng thái Pomodoro hiện tại của phòng và các thông tin thiết lập phiên.
3. Actor thiết lập thời gian tập trung và thời gian nghỉ cho phiên Pomodoro.
4. Actor nhấn chọn “Bắt đầu”.
5. Hệ thống kiểm tra quyền điều khiển Pomodoro của Actor và trạng thái hiện tại của phòng.
6. Hệ thống tạo phiên Pomodoro với các thông số Actor đã thiết lập và ghi nhận thời điểm bắt đầu.
7. Hệ thống chuyển phiên sang trạng thái tập trung và bắt đầu bộ đếm thời gian chung.
8. Hệ thống đồng bộ trạng thái và thời gian của phiên đến các thành viên đang tham gia phòng.
9. Các thành viên theo dõi thời gian tập trung còn lại trên giao diện phòng tự học.
10. Khi thời gian tập trung kết thúc, hệ thống ghi nhận khoảng tập trung đã hoàn thành.
11. Hệ thống chuyển Pomodoro sang trạng thái nghỉ và đồng bộ trạng thái mới đến các thành viên.
12. Khi thời gian nghỉ kết thúc, hệ thống chuyển sang chu kỳ tiếp theo theo thiết lập của phiên.
13. Quá trình tiếp tục cho đến khi phiên Pomodoro hoàn thành hoặc được Actor kết thúc.
Alternative Flow	A1: Actor sử dụng thời gian Pomodoro mặc định
- Tại bước 3, Actor không thay đổi thời gian tập trung và thời gian nghỉ được hệ thống đề xuất.
- Hệ thống sử dụng các giá trị mặc định và Actor tiếp tục thực hiện từ bước 4.
A2: Tạm dừng và tiếp tục phiên Pomodoro
- Trong thời gian Pomodoro đang chạy, Actor nhấn chọn “Tạm dừng”.
- Hệ thống ghi nhận thời gian còn lại, chuyển phiên sang trạng thái tạm dừng và đồng bộ trạng thái này cho các thành viên.
- Khi Actor chọn “Tiếp tục”, hệ thống tính lại mốc thời gian của phiên dựa trên thời gian còn lại và tiếp tục bộ đếm.
- Trạng thái mới được đồng bộ cho các thành viên trong phòng.
A3: Actor kết thúc phiên trước khi hoàn thành
- Trong khi phiên đang hoạt động, Actor chọn “Kết thúc Pomodoro”.
- Hệ thống yêu cầu Actor xác nhận việc kết thúc phiên.
- Actor xác nhận.
- Hệ thống dừng bộ đếm và cập nhật phiên Pomodoro sang trạng thái đã kết thúc.
- Khoảng tập trung chưa hoàn thành tại thời điểm kết thúc không được ghi nhận là một khoảng tập trung hoàn chỉnh. 

Exception Flow	E1: Actor không còn quyền điều khiển Pomodoro
- Tại bước 5, nếu quyền của Actor đã thay đổi và Actor không còn được phép quản lý Pomodoro, hệ thống từ chối yêu cầu bắt đầu hoặc thay đổi phiên.
- Hệ thống tải lại trạng thái Pomodoro hiện tại của phòng và Actor chỉ có thể theo dõi phiên.
E2: Trạng thái Pomodoro đã được thay đổi bởi Actor khác
- Tại bước 5, nếu một thành viên có quyền khác đã thay đổi phiên trước yêu cầu hiện tại của Actor, hệ thống không ghi đè trạng thái mới bằng dữ liệu cũ.
- Hệ thống lấy trạng thái Pomodoro mới nhất, đồng bộ lại giao diện cho Actor và yêu cầu Actor thực hiện thao tác dựa trên trạng thái vừa được cập nhật.
2.4.2.28. Xem trạng thái thành viên trong phòng tự học
Bảng 2.69. Đặc tả use case Xem trạng thái thành viên trong phòng tự học
[UC28]	Xem trạng thái thành viên trong phòng tự học
Actor	Thành viên Workspace
Description	Use Case này cho phép Actor theo dõi danh sách thành viên đang có mặt trong phòng tự học cùng trạng thái hoạt động của từng thành viên như microphone, camera và chia sẻ màn hình. Thông tin được cập nhật trong quá trình các thành viên tham gia và tương tác trong phòng.
Pre-Conditions	Actor đang tham gia phòng tự học.
Post-Conditions	Actor xem được danh sách và trạng thái hiện tại của các thành viên trong phòng. Use Case không làm thay đổi dữ liệu hay trạng thái hoạt động của các thành viên.
 
Main Flow	1. Actor truy cập giao diện phòng tự học mà mình đang tham gia.
2. Hệ thống lấy danh sách các thành viên hiện đang có mặt trong phòng.
3. Hệ thống hiển thị danh sách thành viên cùng trạng thái microphone, camera và chia sẻ màn hình của từng người.
4. Actor xem thông tin trạng thái của các thành viên trong phòng.
5. Khi có thành viên mới tham gia, hệ thống nhận trạng thái tham gia và bổ sung thành viên đó vào danh sách.
6. Khi một thành viên thay đổi trạng thái microphone, camera hoặc chia sẻ màn hình, hệ thống cập nhật trạng thái tương ứng trên giao diện.
7. Khi một thành viên rời phòng, hệ thống loại thành viên đó khỏi danh sách thành viên đang trực tuyến.
8. Actor tiếp tục theo dõi danh sách thành viên trong suốt thời gian tham gia phòng.
Alternative Flow	A1: Phòng chỉ có Actor đang tham gia
- Tại bước 2, nếu không có thành viên nào khác trong phòng, hệ thống chỉ hiển thị Actor trong danh sách thành viên.
- Hệ thống tiếp tục theo dõi trạng thái phòng; khi có thành viên khác tham gia, danh sách được cập nhật theo bước 5 của Main Flow.

Exception Flow	E1: Kết nối thời gian thực bị gián đoạn
- Trong quá trình Actor xem trạng thái thành viên, nếu kết nối với phòng bị gián đoạn, hệ thống tạm thời giữ thông tin gần nhất đã nhận được và không tiếp tục cập nhật trạng thái mới.
- Khi kết nối được khôi phục, hệ thống lấy lại danh sách cùng trạng thái hiện tại của các thành viên thay vì tiếp tục sử dụng dữ liệu cũ.
- Giao diện của Actor được đồng bộ lại theo trạng thái mới nhất của phòng.



2.4.2.29. Tải tài liệu học tập lên kênh
Bảng 2.70. Đặc tả use case Tải tài liệu học tập lên kênh
[UC29]	Tải tài liệu học tập lên kênh
Actor	Chủ Workspace / Thành viên có quyền quản lý tài liệu
Description	Use Case này cho phép Actor tải tài liệu học tập lên một kênh trong Workspace để chia sẻ cho các thành viên. Tài liệu sau khi được lưu sẽ được hệ thống tiếp tục xử lý nội dung nhằm tạo nguồn dữ liệu cho chức năng hỏi đáp của trợ lý AI.
Pre-Conditions	- Actor đã đăng nhập và có quyền quản lý tài liệu tại kênh được chọn.
- Kênh vẫn tồn tại và Actor có quyền truy cập.
Post-Conditions	- Nếu tải lên thành công, tài liệu được lưu và xuất hiện trong danh sách tài liệu của kênh.
- Tài liệu được đưa vào quá trình xử lý nội dung phục vụ RAG. Trạng thái xử lý được cập nhật để xác định tài liệu đang xử lý, đã sẵn sàng hoặc xử lý thất bại.
 
Main Flow	1. Actor truy cập Workspace và chọn kênh cần bổ sung tài liệu.
2. Actor mở khu vực “Tài liệu học tập” của kênh.
3. Actor nhấn chọn “Tải tài liệu lên”.
4. Hệ thống hiển thị giao diện tải tài liệu.
5. Actor lựa chọn tệp tài liệu từ thiết bị.
6. Hệ thống kiểm tra định dạng và dung lượng của tệp được lựa chọn.
7. Hệ thống hiển thị thông tin tệp và cho phép Actor nhập tên hoặc mô tả tài liệu nếu cần.
8. Actor xác nhận tải tài liệu.
9. Hệ thống lưu tệp vào vùng lưu trữ và tạo thông tin tài liệu trong hệ thống.
10. Hệ thống liên kết tài liệu với kênh và ghi nhận Actor là người tải tài liệu lên.
11. Hệ thống cập nhật trạng thái xử lý của tài liệu thành “Đang xử lý” và hiển thị tài liệu trong danh sách của kênh.
12. Hệ thống đưa tài liệu vào quy trình xử lý phục vụ RAG.
13. Hệ thống trích xuất nội dung văn bản từ tài liệu.
14. Hệ thống chia nội dung thành các đoạn phù hợp và lưu thông tin vị trí của từng đoạn trong tài liệu gốc.
15. Hệ thống tạo vector biểu diễn cho các đoạn nội dung và lưu dữ liệu cần thiết để phục vụ truy xuất kiến thức.
16. Khi toàn bộ quá trình xử lý hoàn thành, hệ thống cập nhật trạng thái tài liệu thành “Sẵn sàng”.
17. Tài liệu có thể được trợ lý AI sử dụng làm nguồn kiến thức khi thành viên đặt câu hỏi trong kênh.
Alternative Flow	A1: Actor hủy thao tác trước khi tải lên
- Tại bước 5 hoặc bước 7, Actor chọn “Hủy”.
- Hệ thống đóng giao diện tải tài liệu, không lưu tệp và không tạo thông tin tài liệu mới.
- Actor được đưa trở lại danh sách tài liệu của kênh.
A2: Actor không nhập thông tin mô tả tài liệu
- Tại bước 7, Actor không nhập tên tùy chỉnh hoặc mô tả cho tài liệu.
- Hệ thống sử dụng tên tệp làm tên tài liệu và tiếp tục luồng chính tại bước 8.
A3: Quá trình xử lý RAG chưa hoàn thành
- Sau bước 11, việc tải và lưu tài liệu đã hoàn tất nên Actor không cần chờ quá trình xử lý RAG.
- Actor có thể rời khỏi khu vực tài liệu hoặc tiếp tục sử dụng các chức năng khác của hệ thống.
- Tài liệu vẫn hiển thị với trạng thái “Đang xử lý”.
- Khi quá trình xử lý hoàn thành, hệ thống tự động cập nhật trạng thái tài liệu thành “Sẵn sàng”.
Exception Flow	E1: Định dạng tệp không được hỗ trợ
- Tại bước 6, nếu tệp không thuộc định dạng tài liệu được hệ thống hỗ trợ, hệ thống không cho phép tiếp tục tải lên.
- Hệ thống thông báo định dạng tệp không hợp lệ và yêu cầu Actor lựa chọn một tệp khác.
- Actor quay lại bước 5 để chọn lại tài liệu.
E2: Dung lượng tệp vượt quá giới hạn cho phép
- Tại bước 6, nếu kích thước tệp vượt quá giới hạn, hệ thống hiển thị thông báo dung lượng không hợp lệ.
- Tệp không được tải lên và Actor có thể lựa chọn một tài liệu khác tại bước 5.
E3: Không thể lưu tài liệu
- Tại bước 9, nếu việc lưu tệp không thành công, hệ thống không tạo bản ghi tài liệu hoàn chỉnh trong kênh.
- Hệ thống thông báo tải tài liệu thất bại và Actor có thể thực hiện lại thao tác.
E4: Không thể trích xuất nội dung tài liệu
- Tại bước 13, nếu tệp đã được lưu nhưng hệ thống không thể trích xuất nội dung văn bản, hệ thống không xóa tài liệu đã tải lên.
- Hệ thống cập nhật trạng thái xử lý của tài liệu thành “Xử lý thất bại”.
- Thành viên vẫn có thể truy cập tài liệu gốc nhưng tài liệu chưa được sử dụng làm nguồn kiến thức cho trợ lý AI.
E5: Không thể hoàn thành việc tạo dữ liệu vector
- Tại bước 15, nếu quá trình tạo hoặc lưu dữ liệu vector xảy ra lỗi, hệ thống cập nhật trạng thái xử lý thành “Xử lý thất bại”.
- Các dữ liệu xử lý chưa hoàn chỉnh không được đưa vào phạm vi truy xuất của trợ lý AI.
- Actor có thể thực hiện chức năng xử lý lại tài liệu khi hệ thống hỗ trợ thao tác này.
2.4.2.30. Xem tài liệu học tập
Bảng 2.71. Đặc tả use case Xem tài liệu học tập
[UC30]	Cài đặt kênh
Actor	Thành viên Workspace
Description	Use Case này cho phép Actor xem danh sách và nội dung các tài liệu học tập đã được chia sẻ trong một kênh của Workspace.
Pre-Conditions	- Actor là thành viên của Workspace và có quyền truy cập kênh.
- Kênh có khu vực tài liệu học tập khả dụng.
Post-Conditions	Actor xem được thông tin hoặc nội dung của tài liệu được lựa chọn. Việc xem không làm thay đổi nội dung của tài liệu trong hệ thống.
 
Main Flow	1. Actor truy cập vào một kênh thuộc Workspace.
2. Actor chọn khu vực “Tài liệu học tập”.
3. Hệ thống kiểm tra quyền truy cập kênh của Actor.
4. Hệ thống lấy danh sách tài liệu đang được chia sẻ trong kênh.
5. Hệ thống hiển thị danh sách tài liệu cùng các thông tin cơ bản như tên tài liệu, loại tệp, người tải lên, thời gian tải lên và trạng thái xử lý.
6. Actor chọn một tài liệu muốn xem.
7. Hệ thống kiểm tra tài liệu vẫn tồn tại và Actor được phép truy cập.
8. Hệ thống lấy nội dung của tài liệu được chọn.
9. Hệ thống mở giao diện xem tài liệu và hiển thị nội dung cho Actor.
10. Actor đọc tài liệu và di chuyển giữa các trang hoặc các phần nội dung được hệ thống hỗ trợ.
11. Khi xem xong, Actor đóng tài liệu và hệ thống đưa Actor trở lại danh sách tài liệu của kênh.
Alternative Flow	A1: Kênh chưa có tài liệu học tập
- Tại bước 4, nếu không tìm thấy tài liệu nào trong kênh, hệ thống hiển thị trạng thái danh sách trống và thông báo kênh chưa có tài liệu được chia sẻ.
- Actor vẫn ở khu vực tài liệu và có thể quay lại kênh.
A2: Tài liệu không hỗ trợ xem trực tiếp
- Tại bước 8, nếu loại tệp không được hệ thống hỗ trợ xem trực tiếp trên trình duyệt, hệ thống hiển thị thông tin của tài liệu thay vì mở trình xem.
- Hệ thống cung cấp chức năng tải tài liệu về thiết bị cho Actor.
- Nếu Actor lựa chọn tải về, hệ thống chuyển sang UC31 – Tải tài liệu về.
Exception Flow	E1: Actor không còn quyền truy cập kênh
- Tại bước 3, nếu Actor đã bị loại khỏi Workspace hoặc quyền truy cập kênh đã thay đổi, hệ thống không trả về danh sách tài liệu.
- Hệ thống thông báo Actor không có quyền truy cập và đưa Actor ra khỏi khu vực tài liệu của kênh.
E2: Tài liệu đã bị xóa hoặc không còn khả dụng
- Tại bước 7, nếu tài liệu đã bị xóa sau khi danh sách được hiển thị, hệ thống không mở nội dung tài liệu.
- Hệ thống thông báo tài liệu không còn tồn tại và tải lại danh sách tài liệu mới nhất của kênh.
E3: Không thể lấy nội dung tài liệu
- Tại bước 8, nếu tệp tài liệu tồn tại nhưng hệ thống không thể lấy nội dung để hiển thị, hệ thống thông báo không thể mở tài liệu tại thời điểm hiện tại.
- Actor vẫn ở danh sách tài liệu và có thể thử mở lại hoặc lựa chọn một tài liệu khác.
2.4.2.31. Tải tài liệu học tập về
Bảng 2.72. Đặc tả use case Tải tài liệu học tập về
[UC31]	Tải tài liệu học tập về
Actor	Thành viên Workspace
Description	Use Case này cho phép Actor tải tệp tài liệu học tập đã được chia sẻ trong kênh về thiết bị cá nhân để sử dụng khi học tập.
Pre-Conditions	- Actor là thành viên của Workspace và có quyền truy cập kênh chứa tài liệu.
- Tài liệu cần tải vẫn tồn tại trong hệ thống.
Post-Conditions	Tệp tài liệu được gửi đến thiết bị của Actor. Nội dung tài liệu được lưu trên hệ thống không bị thay đổi.
 
Main Flow	1. Actor truy cập khu vực “Tài liệu học tập” của kênh.
2. Hệ thống hiển thị danh sách các tài liệu hiện có trong kênh.
3. Actor chọn tài liệu muốn tải về.
4. Actor nhấn chọn chức năng “Tải xuống”.
5. Hệ thống kiểm tra quyền truy cập tài liệu của Actor.
6. Hệ thống kiểm tra sự tồn tại của tệp tài liệu trong vùng lưu trữ.
7. Hệ thống gửi tệp tài liệu đến trình duyệt của Actor.
8. Trình duyệt thực hiện tải tệp về thiết bị của Actor.
Alternative Flow	Không có.
Exception Flow	E1: Actor không còn quyền truy cập tài liệu
- Tại bước 5, nếu quyền thành viên hoặc quyền truy cập kênh của Actor đã thay đổi, hệ thống từ chối yêu cầu tải tài liệu.
- Hệ thống thông báo Actor không có quyền thực hiện chức năng.
E2: Tệp tài liệu không còn tồn tại trong vùng lưu trữ
- Tại bước 6, nếu thông tin tài liệu vẫn tồn tại nhưng không tìm thấy tệp tương ứng, hệ thống không thực hiện tải xuống.
- Hệ thống thông báo tài liệu hiện không khả dụng để Actor biết và quay lại danh sách tài liệu.
2.4.2.32. Quản lý tài liệu học tập
Bảng 2.73. Đặc tả use case Quản lý tài liệu học tập
[UC32]	Quản lý tài liệu học tập
Actor	Chủ Workspace / Người có quyền quản lý
Description	Use Case này cho phép Actor quản lý các tài liệu học tập đã được tải lên kênh, bao gồm cập nhật thông tin và xóa những tài liệu không còn cần thiết.
Pre-Conditions	- Actor đã đăng nhập và có quyền quản lý tài liệu trong Workspace.
- Tài liệu cần quản lý thuộc kênh mà Actor có quyền truy cập.
Post-Conditions	Thông tin tài liệu được cập nhật theo thao tác của Actor hoặc tài liệu được loại bỏ khỏi kênh nếu Actor thực hiện xóa. Khi tài liệu bị xóa, dữ liệu được tạo từ tài liệu để phục vụ RAG cũng không còn được sử dụng làm nguồn kiến thức của kênh.
 
Main Flow	1. Actor truy cập khu vực “Tài liệu học tập” của kênh.
2. Hệ thống hiển thị danh sách các tài liệu hiện có.
3. Actor chọn một tài liệu cần quản lý.
4. Hệ thống hiển thị thông tin chi tiết và các chức năng quản lý Actor được phép thực hiện.
5. Actor chọn chức năng chỉnh sửa thông tin tài liệu.
6. Hệ thống hiển thị thông tin hiện tại của tài liệu.
7. Actor thay đổi tên hoặc mô tả tài liệu.
8. Actor xác nhận lưu thay đổi.
9. Hệ thống kiểm tra thông tin được nhập và cập nhật thông tin tài liệu.
10. Hệ thống thông báo cập nhật thành công và hiển thị thông tin mới trong danh sách tài liệu. 
Alternative Flow	A1: Actor xóa tài liệu
- Tại bước 5, Actor chọn chức năng “Xóa tài liệu”.
- Hệ thống hiển thị yêu cầu xác nhận xóa và cảnh báo tài liệu sẽ không còn được sử dụng làm nguồn cho trợ lý AI.
- Actor xác nhận xóa.
- Hệ thống loại tài liệu khỏi kênh, ngừng cho phép thành viên truy cập tệp và loại các dữ liệu RAG được tạo từ tài liệu khỏi phạm vi truy xuất.
- Hệ thống cập nhật lại danh sách tài liệu của kênh.
A2: Actor hủy chỉnh sửa
- Tại bước 7, Actor chọn “Hủy”.
- Hệ thống không lưu các nội dung vừa thay đổi và hiển thị lại thông tin ban đầu của tài liệu.
Exception Flow	E1: Tài liệu đã bị xóa bởi người quản lý khác
- Tại bước 9, nếu tài liệu không còn tồn tại, hệ thống không thực hiện cập nhật.
- Hệ thống thông báo tài liệu đã bị xóa và tải lại danh sách tài liệu mới nhất.
E2: Actor không còn quyền quản lý tài liệu
- Nếu quyền của Actor đã thay đổi trước khi thao tác được xác nhận, hệ thống từ chối cập nhật hoặc xóa tài liệu.
- Hệ thống thông báo Actor không còn quyền thực hiện chức năng và cập nhật lại giao diện theo quyền hiện tại.
2.4.2.33. Đặt câu hỏi cho trợ lý AI dựa trên tài liệu
Bảng 2.74. Đặc tả use case Đặt câu hỏi cho trợ lý AI dựa trên tài liệu
[UC33]	Đặt câu hỏi cho trợ lý AI dựa trên tài liệu
Actor	Thành viên Workspace
Description	Use Case này cho phép Actor đặt câu hỏi cho trợ lý AI trong một kênh. Hệ thống sử dụng các tài liệu học tập đã được xử lý của kênh làm nguồn kiến thức, truy xuất những nội dung có liên quan đến câu hỏi và tạo câu trả lời dựa trên các nội dung tìm được.
Pre-Conditions	- Actor là thành viên của Workspace và có quyền truy cập kênh.
- Kênh có ít nhất một tài liệu đã được xử lý thành công và sẵn sàng làm nguồn dữ liệu cho trợ lý AI.
Post-Conditions	- Câu hỏi và câu trả lời của trợ lý AI được lưu vào lịch sử hỏi đáp của Actor trong kênh.
- Câu trả lời được hiển thị cùng thông tin nguồn tham khảo khi hệ thống tìm được nội dung tài liệu phù hợp.
 
Main Flow	1. Actor truy cập một kênh thuộc Workspace.
2. Actor mở chức năng “Trợ lý AI”.
3. Hệ thống hiển thị giao diện hỏi đáp và lịch sử trao đổi gần nhất của Actor trong kênh.
4. Actor nhập câu hỏi liên quan đến nội dung tài liệu học tập.
5. Actor gửi câu hỏi cho trợ lý AI.
6. Hệ thống kiểm tra quyền truy cập kênh của Actor và xác định các tài liệu đang ở trạng thái sẵn sàng.
7. Hệ thống xử lý câu hỏi của Actor để tạo dữ liệu biểu diễn phục vụ việc tìm kiếm nội dung liên quan.
8. Hệ thống tìm kiếm các đoạn nội dung có mức độ liên quan cao trong dữ liệu tài liệu của kênh.
9. Hệ thống lựa chọn các đoạn nội dung phù hợp cùng thông tin về tài liệu và vị trí nguồn tương ứng.
10. Hệ thống kết hợp câu hỏi của Actor với các nội dung được truy xuất và gửi đến mô hình ngôn ngữ để tạo câu trả lời.
11. Mô hình ngôn ngữ tạo nội dung trả lời dựa trên ngữ cảnh được cung cấp.
12. Hệ thống tiếp nhận câu trả lời và liên kết câu trả lời với các nguồn tài liệu đã được sử dụng.
13. Hệ thống lưu câu hỏi, câu trả lời và thông tin nguồn tham khảo vào lịch sử hỏi đáp của Actor.
14. Hệ thống hiển thị câu trả lời cho Actor cùng các nguồn tham khảo tương ứng.
Alternative Flow	A1: Không tìm thấy nội dung tài liệu đủ liên quan
- Tại bước 8, nếu hệ thống không tìm thấy đoạn tài liệu đáp ứng mức độ liên quan cần thiết, hệ thống không sử dụng nội dung không phù hợp để tạo một câu trả lời khẳng định.
- Hệ thống thông báo chưa tìm thấy thông tin phù hợp trong tài liệu hiện có của kênh và đề nghị Actor diễn đạt lại câu hỏi hoặc kiểm tra nguồn tài liệu.
- Câu hỏi và kết quả xử lý vẫn có thể được ghi nhận trong lịch sử hỏi đáp.
A2: Actor tiếp tục đặt câu hỏi trong cuộc hội thoại hiện tại
- Sau bước 14, Actor nhập một câu hỏi tiếp theo.
- Hệ thống tiếp nhận câu hỏi mới cùng ngữ cảnh hội thoại cần thiết và tiếp tục thực hiện quá trình truy xuất tài liệu.
- Luồng tiếp tục từ bước 5.
Exception Flow	E1: Không có tài liệu nào ở trạng thái sẵn sàng
- Tại bước 6, nếu các tài liệu của kênh vẫn đang xử lý hoặc xử lý thất bại, hệ thống không thực hiện truy xuất RAG.
- Hệ thống thông báo hiện chưa có nguồn tài liệu sẵn sàng để trợ lý AI trả lời câu hỏi.
E2: Không thể hoàn thành quá trình truy xuất dữ liệu
- Tại bước 8, nếu xảy ra lỗi trong quá trình tìm kiếm dữ liệu tài liệu, hệ thống dừng yêu cầu hiện tại.
- Hệ thống thông báo không thể xử lý câu hỏi tại thời điểm đó và Actor có thể thực hiện lại yêu cầu.
E3: Không nhận được kết quả từ mô hình ngôn ngữ
- Tại bước 11, nếu quá trình tạo câu trả lời thất bại hoặc dịch vụ AI không phản hồi, hệ thống không tạo câu trả lời không đầy đủ cho Actor.
- Hệ thống thông báo yêu cầu chưa thể hoàn thành và cho phép Actor gửi lại câu hỏi.
2.4.2.34. Xem nguồn tài liệu tham khảo của câu trả lời AI
Bảng 2.75. Đặc tả use case Xem nguồn tài liệu tham khảo của câu trả lời AI
[UC34]	Xem nguồn tài liệu tham khảo của câu trả lời AI
Actor	Thành viên Workspace
Description	Use Case này cho phép Actor xem tài liệu và vị trí nội dung được trợ lý AI sử dụng làm nguồn tham khảo cho câu trả lời, giúp Actor kiểm tra lại thông tin trong tài liệu học tập gốc.
Pre-Conditions	- Actor đã nhận được một câu trả lời từ trợ lý AI.
- Câu trả lời có ít nhất một nguồn tài liệu tham khảo được hệ thống ghi nhận.
Post-Conditions	Actor xem được thông tin nguồn và nội dung liên quan trong tài liệu gốc mà không làm thay đổi tài liệu.
 
Main Flow	1. Hệ thống hiển thị câu trả lời của trợ lý AI cùng danh sách nguồn tham khảo.
2. Actor chọn một nguồn tham khảo được đính kèm trong câu trả lời.
3. Hệ thống xác định tài liệu và vị trí nội dung tương ứng với nguồn Actor đã chọn.
4. Hệ thống kiểm tra quyền truy cập tài liệu của Actor.
5. Hệ thống mở tài liệu tại trang hoặc khu vực nội dung có liên quan nếu định dạng tài liệu hỗ trợ.
6. Hệ thống làm nổi bật hoặc hiển thị đoạn nội dung đã được sử dụng làm nguồn tham khảo khi khả năng xem tài liệu cho phép.
7. Actor đọc nội dung nguồn và đối chiếu với câu trả lời của trợ lý AI.
Alternative Flow	A1: Không thể mở trực tiếp đúng vị trí của nội dung
- Tại bước 5, nếu hệ thống không hỗ trợ điều hướng trực tiếp đến vị trí của đoạn trích trong loại tài liệu hiện tại, hệ thống mở tài liệu và hiển thị thông tin về nguồn tham khảo đã lưu.
- Actor có thể xem tài liệu hoặc tải tài liệu về để kiểm tra nội dung.
Exception Flow	E1: Tài liệu nguồn đã bị xóa
- Tại bước 3, nếu tài liệu được sử dụng khi tạo câu trả lời trước đó hiện không còn tồn tại, hệ thống không thể mở tài liệu gốc.
- Hệ thống thông báo nguồn tài liệu không còn khả dụng nhưng vẫn giữ nội dung câu trả lời trong lịch sử hỏi đáp.
E2: Actor không còn quyền truy cập tài liệu nguồn
- Tại bước 4, hệ thống từ chối việc mở tài liệu và thông báo Actor không có quyền truy cập nguồn này.


2.4.2.35. Xem lịch sử hỏi đáp AI
Bảng 2.76. Đặc tả use case Xem lịch sử hỏi đáp AI
[UC35]	Xem lịch sử hỏi đáp AI
Actor	Thành viên Workspace
Description	Use Case này cho phép Actor xem lại các câu hỏi và câu trả lời trước đó của mình với trợ lý AI trong kênh. 
Pre-Conditions	Actor đã đăng nhập và có quyền truy cập vào kênh.
Post-Conditions	Lịch sử hỏi đáp được hiển thị cho Actor. Dữ liệu hội thoại không bị thay đổi.
 
Main Flow	1. Actor truy cập chức năng “Trợ lý AI” của kênh.
2. Actor chọn xem lịch sử hỏi đáp.
3. Hệ thống xác định Actor và kênh hiện tại.
4. Hệ thống lấy danh sách các cuộc hội thoại AI trước đó của Actor trong kênh.
5. Hệ thống hiển thị danh sách lịch sử theo thời gian.
6. Actor chọn một cuộc hội thoại muốn xem lại.
7. Hệ thống lấy các câu hỏi, câu trả lời và thông tin nguồn tham khảo thuộc cuộc hội thoại.
8. Hệ thống hiển thị nội dung cuộc hội thoại cho Actor.
9. Actor xem lại nội dung và có thể chọn nguồn tham khảo của câu trả lời thông qua UC34.
Alternative Flow	A1: Actor chưa có lịch sử hỏi đáp trong kênh
- Tại bước 4, nếu không tìm thấy cuộc hội thoại nào, hệ thống hiển thị trạng thái lịch sử trống.
- Actor có thể bắt đầu đặt câu hỏi mới cho trợ lý AI.
Exception Flow	E1: Actor không còn quyền truy cập kênh
- Tại bước 3, nếu Actor không còn quyền truy cập kênh, hệ thống không cung cấp lịch sử hỏi đáp thuộc kênh đó và thông báo quyền truy cập không hợp lệ.
2.4.2.36. Quản lý lịch sử hỏi đáp AI
Bảng 2.77. Đặc tả use case Quản lý lịch sử hỏi đáp AI
[UC36]	Quản lý lịch sử hỏi đáp AI
Actor	Thành viên Workspace
Description	Use Case này cho phép Actor quản lý lịch sử trao đổi của chính mình với trợ lý AI, chủ yếu bao gồm đổi tên cuộc hội thoại và xóa những cuộc hội thoại không còn cần thiết.
Pre-Conditions	Actor có ít nhất một cuộc hội thoại AI đã được lưu và có quyền truy cập cuộc hội thoại đó.
Post-Conditions	Thông tin cuộc hội thoại được cập nhật hoặc cuộc hội thoại được xóa theo lựa chọn của Actor.
 
Main Flow	1. Actor mở danh sách lịch sử hỏi đáp AI.
2. Hệ thống hiển thị các cuộc hội thoại thuộc Actor.
3. Actor chọn một cuộc hội thoại cần quản lý.
4. Actor chọn chức năng đổi tên cuộc hội thoại.
5. Hệ thống hiển thị tên hiện tại.
6. Actor nhập tên mới và xác nhận.
7. Hệ thống kiểm tra nội dung tên mới.
8. Hệ thống cập nhật tên cuộc hội thoại.
9. Hệ thống hiển thị tên mới trong danh sách lịch sử.
Alternative Flow	A1: Actor xóa cuộc hội thoại
- Tại bước 4, Actor chọn “Xóa”.
- Hệ thống yêu cầu Actor xác nhận thao tác.
- Actor xác nhận xóa.
- Hệ thống xóa cuộc hội thoại cùng các câu hỏi, câu trả lời và liên kết nguồn thuộc cuộc hội thoại khỏi lịch sử của Actor.
- Hệ thống cập nhật lại danh sách lịch sử hỏi đáp.
A2: Actor hủy thao tác
- Actor đóng giao diện chỉnh sửa hoặc hủy xác nhận xóa.
- Hệ thống giữ nguyên dữ liệu cuộc hội thoại.
Exception Flow	E1: Cuộc hội thoại không còn tồn tại
- Nếu cuộc hội thoại đã bị xóa trước khi Actor xác nhận thao tác, hệ thống không thực hiện cập nhật.
- Hệ thống thông báo dữ liệu không còn tồn tại và tải lại danh sách lịch sử.


2.4.2.37. Ghi nhận phiên tự học
Bảng 2.78. Đặc tả use case Ghi nhận phiên tự học
[UC37]	Ghi nhận phiên tự học
Actor	Hệ thống
Description	Use Case này mô tả quá trình hệ thống ghi nhận thông tin phiên tự học của người dùng dựa trên thời điểm tham gia và rời phòng tự học. Dữ liệu được sử dụng làm cơ sở cho các chức năng thống kê thời gian học, chuỗi ngày học liên tục và mức độ tập trung.
Pre-Conditions	Người dùng đã tham gia phòng tự học và hệ thống đã ghi nhận thời điểm bắt đầu phiên.
Post-Conditions	Phiên tự học được lưu với thời gian bắt đầu, thời gian kết thúc, thời lượng hợp lệ và các thông tin cần thiết phục vụ thống kê học tập.

 
Main Flow	1. Hệ thống ghi nhận thời điểm người dùng tham gia phòng tự học.
2. Hệ thống tạo phiên tự học tương ứng với người dùng và phòng đang tham gia.
3. Trong thời gian phiên hoạt động, hệ thống ghi nhận các thông tin học tập cần thiết liên quan đến phiên.
4. Khi người dùng rời phòng, hệ thống ghi nhận thời điểm kết thúc.
5. Hệ thống tính tổng thời gian tham gia của phiên.
6. Hệ thống kiểm tra tính hợp lệ của dữ liệu thời gian.
7. Hệ thống cập nhật phiên tự học sang trạng thái đã hoàn thành.
8. Dữ liệu phiên được đưa vào nguồn dữ liệu phục vụ các chức năng thống kê học tập.
Alternative Flow	A1: Người dùng mất kết nối và kết nối lại trong thời gian cho phép
- Trong quá trình phiên đang hoạt động, hệ thống phát hiện kết nối của người dùng bị gián đoạn.
- Hệ thống giữ phiên ở trạng thái chờ kết nối lại trong khoảng thời gian quy định.
- Nếu người dùng quay lại trong khoảng thời gian này, hệ thống tiếp tục phiên hiện tại thay vì tạo một phiên mới.
- Thời gian phiên tiếp tục được ghi nhận theo quy tắc của hệ thống.
Exception Flow	E1: Người dùng mất kết nối và không quay lại
- Sau khoảng thời gian chờ, nếu người dùng không kết nối lại, hệ thống tự động kết thúc phiên.
- Hệ thống sử dụng thời điểm hoạt động hợp lệ cuối cùng để xác định thời gian kết thúc và lưu phiên.
E2: Dữ liệu thời gian của phiên không hợp lệ
- Tại bước 6, nếu thời điểm kết thúc hoặc dữ liệu phiên không đáp ứng điều kiện ghi nhận, hệ thống không đưa dữ liệu sai vào kết quả thống kê.
- Phiên được đánh dấu để xử lý hoặc loại khỏi phép tính thống kê tùy theo trạng thái dữ liệu.


2.4.2.38. Xem thống kê thời gian tự học
Bảng 2.79. Đặc tả use case Xem thống kê thời gian tự học
[UC38]	Xem thống kê thời gian tự học
Actor	Người dùng
Description	Use Case này cho phép Actor theo dõi tổng thời gian tự học đã được hệ thống ghi nhận theo các khoảng thời gian khác nhau, giúp Actor đánh giá quá trình duy trì hoạt động học tập của mình.
Pre-Conditions	Actor đã đăng nhập vào hệ thống.
Post-Conditions	Các số liệu thống kê thời gian tự học trong khoảng thời gian được lựa chọn được hiển thị cho Actor.
 
Main Flow	1. Actor mở khu vực thống kê học tập cá nhân.
2. Hệ thống hiển thị khoảng thời gian thống kê mặc định.
3. Actor lựa chọn khoảng thời gian muốn xem.
4. Hệ thống lấy các phiên tự học hợp lệ của Actor trong khoảng thời gian tương ứng.
5. Hệ thống tổng hợp thời lượng tự học từ các phiên.
6. Hệ thống tính các số liệu cần thiết theo ngày hoặc khoảng thời gian được lựa chọn.
7. Hệ thống hiển thị tổng thời gian tự học và dữ liệu thống kê dưới dạng phù hợp trên giao diện.
8. Actor xem và đối chiếu hoạt động học tập của mình.
Alternative Flow	A1: Actor thay đổi khoảng thời gian thống kê
- Sau khi xem kết quả, Actor lựa chọn một khoảng thời gian khác.
- Hệ thống thực hiện lại việc lấy và tổng hợp dữ liệu theo khoảng thời gian mới, sau đó cập nhật kết quả trên giao diện.
A2: Không có phiên tự học trong khoảng thời gian được chọn
- Tại bước 4, nếu không có dữ liệu phiên tự học, hệ thống hiển thị thời gian học bằng 0 và trạng thái chưa có dữ liệu thay vì hiển thị lỗi.
Exception Flow	Không có.


2.4.2.39. Theo dõi chuỗi ngày học liên tục (Streak)
Bảng 2.80. Đặc tả use case Theo dõi chuỗi ngày học liên tục (Streak)
[UC39]	Theo dõi chuỗi ngày học liên tục (Streak)
Actor	Người dùng
Description	Use Case này cho phép Actor theo dõi số ngày học liên tục dựa trên các phiên tự học hợp lệ đã được hệ thống ghi nhận.
Pre-Conditions	Actor đã đăng nhập vào hệ thống.
Post-Conditions	Hệ thống hiển thị chuỗi ngày học hiện tại và các thông tin liên quan đến quá trình duy trì hoạt động học tập của Actor.
 
Main Flow	1. Actor truy cập khu vực thống kê học tập cá nhân.
2. Hệ thống lấy các ngày có phiên tự học hợp lệ của Actor.
3. Hệ thống kiểm tra điều kiện một ngày được tính là ngày học hợp lệ theo quy tắc đã thiết lập.
4. Hệ thống sắp xếp và đối chiếu các ngày học liên tiếp.
5. Hệ thống tính chuỗi ngày học liên tục hiện tại của Actor.
6. Hệ thống lấy chuỗi ngày học dài nhất đã đạt được nếu hệ thống có lưu hoặc tính chỉ số này.
7. Hệ thống hiển thị số ngày Streak hiện tại và lịch sử ngày học trên giao diện.
8. Actor xem quá trình duy trì thói quen tự học của mình.
Alternative Flow	A1: Actor chưa có ngày học hợp lệ
- Tại bước 2, nếu chưa có phiên tự học nào đáp ứng điều kiện, hệ thống hiển thị Streak hiện tại bằng 0.
- Hệ thống hiển thị trạng thái phù hợp để Actor biết chưa hình thành chuỗi ngày học.
A2: Chuỗi ngày học đã bị gián đoạn
- Tại bước 4, nếu giữa ngày học gần nhất và ngày hiện tại tồn tại ngày không đáp ứng điều kiện duy trì Streak, hệ thống kết thúc chuỗi trước đó.
- Streak hiện tại được tính lại dựa trên chuỗi ngày học liên tục gần nhất.
Exception Flow	Không có.


2.4.2.40. Xem thống kê mức độ tập trung
Bảng 2.78. Đặc tả use case Xem thống kê mức độ tập trung
[UC40]	Xem thống kê mức độ tập trung
Actor	Người dùng
Description	Use Case này cho phép Actor xem các chỉ số phản ánh mức độ duy trì tập trung trong quá trình tự học. Kết quả được tính từ dữ liệu phiên tự học và các khoảng Pomodoro đã hoàn thành, không sử dụng camera để nhận diện hoặc đánh giá hành vi của người học.
Pre-Conditions	Actor đã đăng nhập và hệ thống có dữ liệu học tập của Actor trong khoảng thời gian cần thống kê.
Post-Conditions	Các chỉ số tập trung được tính toán từ dữ liệu học tập hợp lệ và hiển thị cho Actor.
 
Main Flow	1. Actor truy cập khu vực thống kê học tập.
2. Actor chọn mục thống kê mức độ tập trung.
3. Hệ thống hiển thị khoảng thời gian thống kê mặc định.
4. Actor lựa chọn khoảng thời gian cần xem.
5. Hệ thống lấy các phiên tự học và dữ liệu Pomodoro của Actor trong khoảng thời gian được chọn.
6. Hệ thống xác định số khoảng tập trung Pomodoro đã hoàn thành, số khoảng bị kết thúc trước thời hạn và thời gian tập trung hợp lệ.
7. Hệ thống tổng hợp các dữ liệu trên thành các chỉ số phản ánh mức độ duy trì tập trung của Actor.
8. Hệ thống hiển thị kết quả thống kê và các thông tin liên quan trên giao diện.
9. Actor xem kết quả để đánh giá quá trình tự học của mình.
Alternative Flow	A1: Không có đủ dữ liệu để tính chỉ số
- Tại bước 5, nếu Actor chưa có phiên Pomodoro hoặc dữ liệu học tập phù hợp trong khoảng thời gian đã chọn, hệ thống không tạo ra chỉ số tập trung thiếu cơ sở.
- Hệ thống hiển thị trạng thái chưa có đủ dữ liệu để thống kê.
A2: Actor thay đổi khoảng thời gian
- Actor lựa chọn khoảng thời gian thống kê khác.
- Hệ thống lấy lại dữ liệu, tính toán các chỉ số theo khoảng thời gian mới và cập nhật kết quả trên giao diện.
Exception Flow	Không có.



2.4.2.41. Báo cáo nội dung/tài liệu vi phạm
Bảng 2.78. Đặc tả use case Báo cáo nội dung/tài liệu vi phạm
[UC41]	Báo cáo nội dung/tài liệu vi phạm
Actor	Người dùng
Description	Use Case này cho phép Actor gửi báo cáo đối với nội dung hoặc tài liệu mà Actor cho rằng vi phạm quy định của nền tảng. Báo cáo được chuyển đến Quản trị viên để xem xét và xử lý.
Pre-Conditions	- Actor đã đăng nhập.
- Nội dung hoặc tài liệu cần báo cáo vẫn tồn tại và Actor có quyền xem nội dung đó.
Post-Conditions	Báo cáo của Actor được ghi nhận với nội dung cần xem xét, lý do báo cáo, người gửi và trạng thái chờ xử lý.
 
Main Flow	1. Actor truy cập nội dung hoặc tài liệu muốn báo cáo.
2. Actor chọn chức năng “Báo cáo vi phạm”.
3. Hệ thống hiển thị biểu mẫu báo cáo.
4. Actor lựa chọn lý do báo cáo.
5. Actor nhập nội dung mô tả bổ sung nếu cần.
6. Actor nhấn chọn “Gửi báo cáo”.
7. Hệ thống kiểm tra thông tin báo cáo.
8. Hệ thống tạo báo cáo, liên kết với nội dung bị báo cáo và Actor gửi báo cáo.
9. Hệ thống đặt trạng thái báo cáo thành “Chờ xử lý”.
10. Hệ thống thông báo Actor đã gửi báo cáo thành công.
Alternative Flow	A1: Actor hủy gửi báo cáo
- Tại bước 4 hoặc bước 5, Actor chọn “Hủy”.
- Hệ thống đóng biểu mẫu và không tạo báo cáo mới.
Exception Flow	E1: Actor chưa lựa chọn lý do báo cáo
- Tại bước 7, nếu lý do là thông tin bắt buộc nhưng Actor chưa lựa chọn, hệ thống không tạo báo cáo.
- Hệ thống thông báo Actor bổ sung lý do và quay lại biểu mẫu.
E2: Nội dung đã bị xóa trước khi gửi báo cáo
- Tại bước 7, nếu đối tượng cần báo cáo không còn tồn tại, hệ thống không tạo báo cáo mới đối với nội dung đó.
- Hệ thống thông báo nội dung không còn khả dụng và đóng biểu mẫu báo cáo.


2.4.2.42. Quản lý người dùng
Bảng 2.78. Đặc tả use case Quản lý người dùng
[UC42]	Quản lý người dùng
Actor	Quản trị viên
Description	Use Case này cho phép Quản trị viên xem và quản lý các tài khoản người dùng trên toàn hệ thống, bao gồm tìm kiếm thông tin và thay đổi trạng thái hoạt động của tài khoản khi cần thiết.
Pre-Conditions	Quản trị viên đã đăng nhập vào khu vực quản trị với quyền hợp lệ.
Post-Conditions	Thông tin hoặc trạng thái tài khoản được cập nhật theo thao tác quản trị đã được xác nhận.
 
Main Flow	1. Quản trị viên truy cập chức năng “Quản lý người dùng”.
2. Hệ thống lấy và hiển thị danh sách tài khoản người dùng.
3. Quản trị viên tìm kiếm hoặc lọc danh sách theo thông tin cần thiết.
4. Hệ thống hiển thị các tài khoản phù hợp với điều kiện tìm kiếm.
5. Quản trị viên chọn một tài khoản.
6. Hệ thống hiển thị thông tin chi tiết và trạng thái hiện tại của tài khoản.
7. Quản trị viên chọn thay đổi trạng thái tài khoản.
8. Hệ thống yêu cầu xác nhận thao tác.
9. Quản trị viên xác nhận.
10. Hệ thống cập nhật trạng thái tài khoản và ghi nhận thao tác quản trị.
11. Hệ thống thông báo cập nhật thành công và hiển thị trạng thái mới.
Alternative Flow	A1: Quản trị viên mở lại tài khoản đang bị khóa
- Tại bước 7, nếu tài khoản đang bị khóa, Quản trị viên chọn chức năng mở khóa.
- Hệ thống yêu cầu xác nhận và sau khi được xác nhận sẽ chuyển tài khoản về trạng thái hoạt động.
- Người dùng có thể tiếp tục sử dụng tài khoản theo quyền hiện có.

A2: Không tìm thấy người dùng phù hợp
- Tại bước 4, nếu không có tài khoản nào phù hợp với điều kiện tìm kiếm, hệ thống hiển thị danh sách trống.
- Quản trị viên có thể thay đổi từ khóa hoặc điều kiện lọc để tìm kiếm lại.
Exception Flow	E1: Tài khoản đã thay đổi trạng thái trước khi xác nhận
- Tại bước 10, nếu trạng thái tài khoản đã được một Quản trị viên khác thay đổi, hệ thống không ghi đè dữ liệu một cách tự động.
- Hệ thống tải lại trạng thái mới nhất và yêu cầu Quản trị viên kiểm tra trước khi thực hiện thao tác tiếp theo.

E2: Quản trị viên thực hiện thao tác không được phép
- Nếu thao tác vượt quá quyền quản trị được cấp, hệ thống từ chối yêu cầu và giữ nguyên trạng thái tài khoản.


2.4.2.43. Quản lý Workspace toàn hệ thống
Bảng 2.78. Đặc tả use case Quản lý Workspace toàn hệ thống
[UC43]	Quản lý Workspace toàn hệ thống
Actor	Quản trị viên
Description	Use Case này cho phép Quản trị viên theo dõi và quản lý các Workspace được tạo trên nền tảng nhằm hỗ trợ xử lý các trường hợp vi phạm hoặc Workspace không còn phù hợp với quy định của hệ thống.
Pre-Conditions	Quản trị viên đã đăng nhập và có quyền quản lý Workspace toàn hệ thống.
Post-Conditions	Workspace được giữ nguyên hoặc được thay đổi trạng thái theo quyết định quản trị. Các thao tác quản lý được hệ thống ghi nhận.
 
Main Flow	1. Quản trị viên truy cập chức năng “Quản lý Workspace”.
2. Hệ thống hiển thị danh sách các Workspace trên nền tảng.
3. Quản trị viên tìm kiếm hoặc lọc Workspace cần kiểm tra.
4. Quản trị viên chọn một Workspace.
5. Hệ thống hiển thị thông tin Workspace, chủ sở hữu, trạng thái và các thông tin quản trị liên quan.
6. Quản trị viên xem xét thông tin của Workspace.
7. Quản trị viên lựa chọn thay đổi trạng thái hoạt động của Workspace khi có căn cứ xử lý.
8. Hệ thống yêu cầu Quản trị viên xác nhận thao tác.
9. Quản trị viên xác nhận.
10. Hệ thống cập nhật trạng thái Workspace và ghi nhận thao tác quản trị.
11. Hệ thống cập nhật lại thông tin Workspace trên giao diện.
Alternative Flow	A1: Quản trị viên khôi phục Workspace đã bị vô hiệu hóa
- Tại bước 7, Quản trị viên chọn khôi phục một Workspace đang bị vô hiệu hóa.
- Hệ thống hiển thị yêu cầu xác nhận.
- Sau khi Quản trị viên xác nhận, hệ thống chuyển Workspace về trạng thái hoạt động và cập nhật quyền truy cập tương ứng.
A2: Quản trị viên chỉ xem thông tin Workspace
- Sau bước 6, nếu không cần thực hiện biện pháp quản lý, Quản trị viên đóng trang chi tiết.
- Hệ thống không thay đổi trạng thái hoặc dữ liệu Workspace.
Exception Flow	E1: Workspace không còn tồn tại
- Tại bước 5 hoặc bước 10, nếu Workspace đã bị chủ sở hữu xóa trước đó, hệ thống không thực hiện thao tác quản lý.
- Hệ thống thông báo Workspace không còn tồn tại và cập nhật danh sách.
E2: Trạng thái Workspace đã được thay đổi
- Nếu một Quản trị viên khác đã xử lý Workspace trước yêu cầu hiện tại, hệ thống tải trạng thái mới nhất thay vì ghi đè bằng trạng thái cũ.
- Quản trị viên xem lại thông tin trước khi quyết định có tiếp tục thao tác hay không.


2.4.2.44. Xử lý báo cáo vi phạm
Bảng 2.78. Đặc tả use case Xử lý báo cáo vi phạm
[UC44]	Xử lý báo cáo vi phạm
Actor	Quản trị viên
Description	Use Case này cho phép Quản trị viên tiếp nhận và xử lý các báo cáo vi phạm do người dùng gửi. Quản trị viên xem nội dung bị báo cáo, lý do báo cáo và quyết định biện pháp xử lý phù hợp.
Pre-Conditions	- Quản trị viên đã đăng nhập và có quyền xử lý báo cáo.
- Hệ thống có báo cáo đang chờ xử lý.
Post-Conditions	- Báo cáo được cập nhật trạng thái xử lý cùng kết quả giải quyết.
- Nếu xác định có vi phạm, nội dung liên quan được xử lý theo quyết định của Quản trị viên.
- Thao tác xử lý được ghi nhận để phục vụ quản lý hệ thống.
 
Main Flow	1. Quản trị viên truy cập chức năng “Báo cáo vi phạm”.
2. Hệ thống hiển thị danh sách các báo cáo đang chờ xử lý.
3. Quản trị viên chọn một báo cáo.
4. Hệ thống hiển thị người gửi báo cáo, lý do, mô tả, thời gian gửi và thông tin đối tượng bị báo cáo.
5. Hệ thống hiển thị nội dung hoặc tài liệu liên quan để Quản trị viên kiểm tra.
6. Quản trị viên xem xét nội dung và thông tin báo cáo.
7. Quản trị viên xác định nội dung có vi phạm quy định của nền tảng.
8. Quản trị viên lựa chọn biện pháp xử lý phù hợp đối với nội dung vi phạm.
9. Hệ thống hiển thị thông tin xác nhận xử lý.
10. Quản trị viên xác nhận quyết định.
11. Hệ thống thực hiện biện pháp xử lý đối với đối tượng bị báo cáo.
12. Hệ thống cập nhật báo cáo sang trạng thái “Đã xử lý” và lưu kết quả xử lý.
13. Hệ thống ghi nhận Quản trị viên và thời điểm thực hiện thao tác.
14. Hệ thống cập nhật lại danh sách báo cáo.
Alternative Flow	A1: Báo cáo không có vi phạm
- Tại bước 7, nếu Quản trị viên xác định nội dung không vi phạm quy định, Quản trị viên lựa chọn kết quả “Không vi phạm”.
- Hệ thống không thay đổi nội dung hoặc tài liệu bị báo cáo.
- Hệ thống cập nhật báo cáo sang trạng thái “Đã xử lý” và lưu kết quả không vi phạm.
- Luồng tiếp tục tại bước 13 của Main Flow.
A2: Quản trị viên cần xem thêm thông tin trước khi quyết định
- Tại bước 6, Quản trị viên chưa đủ thông tin để kết luận.
- Quản trị viên đóng màn hình xử lý hoặc giữ báo cáo ở trạng thái chờ xử lý.
- Hệ thống không áp dụng biện pháp xử lý đối với nội dung bị báo cáo và báo cáo có thể được xem xét lại sau.
Exception Flow	E1: Nội dung bị báo cáo đã bị xóa
- Tại bước 5, nếu nội dung hoặc tài liệu không còn tồn tại, hệ thống thông báo cho Quản trị viên.
- Quản trị viên vẫn có thể xem các thông tin báo cáo đã được lưu và xác định kết quả xử lý phù hợp.
E2: Báo cáo đã được Quản trị viên khác xử lý
- Trước bước 11, nếu hệ thống phát hiện trạng thái báo cáo không còn là “Chờ xử lý”, hệ thống không thực hiện lại biện pháp dựa trên dữ liệu cũ.
- Hệ thống hiển thị kết quả xử lý mới nhất và thông tin người đã xử lý báo cáo.


2.4.2.45. Xem thống kê và giám sát hệ thống
Bảng 2.78. Đặc tả use case Xem thống kê và giám sát hệ thống
[UC45]	Xem thống kê và giám sát hệ thống
Actor	Quản trị viên
Description	Use Case này cho phép Quản trị viên theo dõi các số liệu tổng quan về hoạt động của nền tảng như người dùng, Workspace, tài liệu, hoạt động học tập và báo cáo vi phạm nhằm hỗ trợ việc quản lý hệ thống.
Pre-Conditions	Quản trị viên đã đăng nhập vào khu vực quản trị.
Post-Conditions	Các số liệu thống kê theo phạm vi và khoảng thời gian được lựa chọn được hiển thị cho Quản trị viên. Use Case không làm thay đổi dữ liệu nghiệp vụ của hệ thống.

 
Main Flow	1. Quản trị viên truy cập trang tổng quan quản trị hệ thống.
2. Hệ thống hiển thị phạm vi thời gian thống kê mặc định.
3. Hệ thống lấy dữ liệu liên quan đến người dùng, Workspace, tài liệu, hoạt động tự học và báo cáo vi phạm.
4. Hệ thống tổng hợp các dữ liệu theo phạm vi thời gian hiện tại.
5. Hệ thống tính toán các chỉ số tổng quan cần hiển thị.
6. Hệ thống hiển thị các số liệu và biểu đồ thống kê trên trang quản trị.
7. Quản trị viên xem các chỉ số hoạt động của nền tảng.
8. Quản trị viên lựa chọn một nhóm thống kê cần xem chi tiết.
9. Hệ thống lấy dữ liệu chi tiết của nhóm được lựa chọn và hiển thị cho Quản trị viên.
Alternative Flow	A1: Quản trị viên thay đổi khoảng thời gian thống kê
- Quản trị viên lựa chọn khoảng thời gian khác trên giao diện.
- Hệ thống lấy và tổng hợp lại dữ liệu trong phạm vi mới.
- Các số liệu và biểu đồ được cập nhật theo khoảng thời gian Quản trị viên lựa chọn.
A2: Không có dữ liệu đối với một nhóm thống kê
- Nếu một nhóm không có dữ liệu trong khoảng thời gian đang xem, hệ thống hiển thị giá trị bằng 0 hoặc trạng thái chưa có dữ liệu.
- Các nhóm thống kê khác vẫn được hiển thị bình thường.
Exception Flow	Không có.

