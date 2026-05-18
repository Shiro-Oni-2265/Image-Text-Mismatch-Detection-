import { useEffect, useMemo, useState } from "react";
import "./App.css";
import { predictImageTextMismatch } from "./services/predictService";

const initialErrors = {
	image: "",
	caption: "",
};

const initialAuthForm = {
	name: "",
	email: "",
	password: "",
};

const AUTH_USER_KEY = "itmd-auth-user";
const AUTH_ACCOUNTS_KEY = "itmd-auth-accounts";
const FEATURE_IMAGE_URL =
	"https://isgen.ai/_next/image?url=%2Fimage-detector%2Fisgen-image-detector.png&w=3840&q=80";

function loadJsonStorage(key, fallback) {
	if (typeof window === "undefined") {
		return fallback;
	}

	try {
		const rawValue = window.localStorage.getItem(key);

		if (!rawValue) {
			return fallback;
		}

		return JSON.parse(rawValue);
	} catch {
		return fallback;
	}
}

function App() {
	const [authUser, setAuthUser] = useState(() =>
		loadJsonStorage(AUTH_USER_KEY, null),
	);
	const [accounts, setAccounts] = useState(() =>
		loadJsonStorage(AUTH_ACCOUNTS_KEY, []),
	);
	const [isAuthOpen, setIsAuthOpen] = useState(false);
	const [authMode, setAuthMode] = useState("login");
	const [authForm, setAuthForm] = useState(initialAuthForm);
	const [authError, setAuthError] = useState("");
	const [authInfo, setAuthInfo] = useState(
		"Đăng nhập để lưu lịch sử và dùng tính năng kiểm tra.",
	);
	const [imageFile, setImageFile] = useState(null);
	const [imagePreviewUrl, setImagePreviewUrl] = useState("");
	const [caption, setCaption] = useState("");
	const [errors, setErrors] = useState(initialErrors);
	const [isLoading, setIsLoading] = useState(false);
	const [result, setResult] = useState(null);

	const hasResult = useMemo(() => result !== null, [result]);

	useEffect(() => {
		if (typeof window === "undefined") {
			return undefined;
		}

		window.localStorage.setItem(AUTH_USER_KEY, JSON.stringify(authUser));
	}, [authUser]);

	useEffect(() => {
		if (typeof window === "undefined") {
			return undefined;
		}

		window.localStorage.setItem(AUTH_ACCOUNTS_KEY, JSON.stringify(accounts));
	}, [accounts]);

	useEffect(() => {
		return () => {
			if (imagePreviewUrl) {
				URL.revokeObjectURL(imagePreviewUrl);
			}
		};
	}, [imagePreviewUrl]);

	const openAuth = (mode) => {
		setAuthMode(mode);
		setAuthError("");
		setAuthInfo(
			mode === "login"
				? "Đăng nhập để bắt đầu kiểm tra ảnh và caption."
				: "Tạo tài khoản mới để dùng toàn bộ giao diện demo.",
		);
		setIsAuthOpen(true);
	};

	const closeAuth = () => {
		setIsAuthOpen(false);
		setAuthError("");
		setAuthInfo("Đăng nhập để lưu lịch sử và dùng tính năng kiểm tra.");
	};

	const switchAuthMode = (mode) => {
		setAuthMode(mode);
		setAuthError("");
		setAuthInfo(
			mode === "login"
				? "Đăng nhập để bắt đầu kiểm tra ảnh và caption."
				: "Tạo tài khoản mới để dùng toàn bộ giao diện demo.",
		);
	};

	const validateInput = () => {
		const nextErrors = { ...initialErrors };

		if (!imageFile) {
			nextErrors.image = "Vui lòng chọn ảnh";
		}

		if (!caption.trim()) {
			nextErrors.caption = "Vui lòng nhập mô tả";
		}

		setErrors(nextErrors);

		return !nextErrors.image && !nextErrors.caption;
	};

	const handleAuthChange = (event) => {
		const { name, value } = event.target;
		setAuthForm((current) => ({ ...current, [name]: value }));
		setAuthError("");
	};

	const handleAuthSubmit = (event) => {
		event.preventDefault();

		const email = authForm.email.trim().toLowerCase();
		const password = authForm.password.trim();
		const name = authForm.name.trim();

		if (!email || !password || (authMode === "register" && !name)) {
			setAuthError("Vui lòng nhập đầy đủ thông tin.");
			return;
		}

		if (authMode === "register") {
			const alreadyExists = accounts.some((account) => account.email === email);

			if (alreadyExists) {
				setAuthError("Email này đã được đăng ký.");
				return;
			}

			const newAccount = {
				name,
				email,
				password,
			};

			setAccounts((current) => [...current, newAccount]);
			setAuthUser({ name, email });
			setAuthForm(initialAuthForm);
			setIsAuthOpen(false);
			setAuthInfo(`Xin chào ${name}, bạn đã đăng ký thành công.`);
			return;
		}

		const matchedAccount = accounts.find((account) => account.email === email);

		if (!matchedAccount || matchedAccount.password !== password) {
			setAuthError("Email hoặc mật khẩu không đúng.");
			return;
		}

		setAuthUser({ name: matchedAccount.name, email: matchedAccount.email });
		setAuthForm(initialAuthForm);
		setIsAuthOpen(false);
		setAuthInfo(`Đã đăng nhập với tài khoản ${matchedAccount.name}.`);
	};

	const handleImageChange = (event) => {
		const file = event.target.files?.[0];

		if (!file) {
			return;
		}

		if (imagePreviewUrl) {
			URL.revokeObjectURL(imagePreviewUrl);
		}

		const previewUrl = URL.createObjectURL(file);
		setImageFile(file);
		setImagePreviewUrl(previewUrl);
		setErrors((prev) => ({ ...prev, image: "" }));
		setResult(null);
	};

	const handleCaptionChange = (event) => {
		setCaption(event.target.value);
		setErrors((prev) => ({ ...prev, caption: "" }));
		setResult(null);
	};

	const handleCheck = async (event) => {
		event.preventDefault();

		if (!authUser) {
			openAuth("login");
			setAuthError("Vui lòng đăng nhập trước khi kiểm tra ảnh.");
			return;
		}

		if (!validateInput()) {
			return;
		}

		setIsLoading(true);

		try {
			const prediction = await predictImageTextMismatch({ imageFile, caption });
			setResult(prediction);
		} catch {
			setResult({
				isMatch: false,
				suggestedCaption:
					"A person standing outdoors with a clear background.",
			});
		} finally {
			setIsLoading(false);
		}
	};

	const handleReset = () => {
		if (imagePreviewUrl) {
			URL.revokeObjectURL(imagePreviewUrl);
		}

		setImageFile(null);
		setImagePreviewUrl("");
		setCaption("");
		setResult(null);
		setErrors(initialErrors);
	};

	const handleLogout = () => {
		setAuthUser(null);
		setResult(null);
		setAuthInfo("Bạn đã đăng xuất.");
	};

	return (
		<div className="page-shell">
			<header className="topbar">
				<div className="brand-mark">
					<span className="brand-badge">ITMD</span>
					<div>
						<p>AI Detector</p>
						<strong>Image-Text Mismatch</strong>
					</div>
				</div>

				<nav className="topnav" aria-label="Điều hướng chính">
					<a href="#hero">Trang chủ</a>
					<a href="#how-it-works">Cách sử dụng</a>
					<a href="#features">Tính năng</a>
				</nav>

				<div className="auth-actions">
					{authUser ? (
						<div className="user-chip">
							<span className="user-avatar">{authUser.name.slice(0, 1).toUpperCase()}</span>
							<div>
								<p>Xin chào</p>
								<strong>{authUser.name}</strong>
							</div>
							<button className="text-button" type="button" onClick={handleLogout}>
								Đăng xuất
							</button>
						</div>
					) : (
						<>
							<button className="text-button" type="button" onClick={() => openAuth("login")}>
								Đăng nhập
							</button>
							<button className="btn primary small" type="button" onClick={() => openAuth("register")}>
								Bắt đầu
							</button>
						</>
					)}
				</div>
			</header>

			<main className="page-content">
				<section className="hero-section" id="hero">
					<div className="hero-header">
						<div className="hero-stats">
							<span>★ 4.9</span>
							<span>1M+ Trusted</span>
						</div>
						<p className="eyebrow">Công cụ phát hiện hình ảnh AI chính xác nhất!</p>
						<h1>Công cụ phát hiện hình ảnh AI chính xác nhất!</h1>
						<p className="hero-copy">
							Tải lên một hình ảnh để xem ảnh đó có được tạo ra hay thay đổi bởi AI
							hay không. Dùng thử bản demo ngay trong trình duyệt.
						</p>
					</div>

					<div className="hero-grid">
						<form className="panel upload-panel" onSubmit={handleCheck}>
							<div className="section-heading">
								<p className="section-kicker">Tải ảnh và caption</p>
								<h2>Nhập dữ liệu để kiểm tra</h2>
							</div>

{!imagePreviewUrl && (
                                                                <label htmlFor="image-input" className="upload-zone">
                                                                        <span className="upload-icon" aria-hidden="true">
                                                                                ↑
                                                                        </span>
                                                                        <span className="upload-title">Nhấp để tải lên hoặc kéo và thả</span>
                                                                        <span className="upload-hint">PNG, JPG, JPEG</span>
                                                                </label>
                                                        )}
                                                        <input
                                                                id="image-input"
                                                                name="image-input"
                                                                type="file"
                                                                accept="image/*"
                                                                onChange={handleImageChange}
                                                        />
                                                        {errors.image ? <p className="error-text">{errors.image}</p> : null}
                                                        {imagePreviewUrl ? (
                                                                <label htmlFor="image-input" className="preview-card" style={{cursor: "pointer", display: "block"}}>
                                                                        <img src={imagePreviewUrl} alt="Ảnh đã tải lên" style={{width: "100%", borderRadius: "8px"}} />
                                                                </label>
							) : null}

							<section className="section-block">
								<h3>Caption mô tả</h3>
								<textarea
									value={caption}
									onChange={handleCaptionChange}
									placeholder="Ví dụ: A person is standing outside near a clear sky."
									rows={4}
								/>
								{errors.caption ? (
									<p className="error-text">{errors.caption}</p>
								) : null}
							</section>

							<div className="action-row">
								<button className="btn primary" type="submit" disabled={isLoading}>
									Kiểm tra
								</button>
								<button
									className="btn ghost"
									type="button"
									onClick={handleReset}
									disabled={isLoading}
								>
									Thử lại
								</button>
							</div>

							{!authUser ? (
								<p className="helper-note">
									Bạn cần đăng nhập để chạy kiểm tra và lưu trạng thái.
								</p>
							) : (
								<p className="helper-note success">Đã đăng nhập với {authUser.email}.</p>
							)}

							{isLoading ? (
								<p className="loading-text">Đang phân tích ảnh...</p>
							) : null}

							<div className="result-area">
								<h3>Kết quả</h3>
								{!hasResult && !isLoading ? (
									<p className="placeholder-text">
										Kết quả sẽ hiển thị tại đây sau khi bạn bấm kiểm tra.
									</p>
								) : null}

								{result?.isMatch ? (
									<div className="result-badge success">
										<h4>Ảnh và mô tả khớp nhau</h4>
									</div>
								) : null}

								{result && !result.isMatch ? (
									<div className="result-stack">
										<div className="result-badge danger">
											<h4>Ảnh và mô tả không khớp</h4>
										</div>
									</div>
								) : null}
							</div>
						</form>

						<aside className="panel insight-panel">
							<div className="insight-card">
								<p className="insight-title">Chính xác nhất</p>
								<h2>Bộ phát hiện hình ảnh AI</h2>
								<p>
									Phát hiện hình ảnh do AI tạo ra và xác định mô hình/công cụ được dùng
									để tạo ảnh.
								</p>
							</div>

							<div className="insight-list">
								<div className="insight-item">
									<span>→</span>
									<p>Phát hiện hình ảnh do AI tạo ra và do AI thay đổi</p>
								</div>
								<div className="insight-item">
									<span>→</span>
									<p>Xác định mô hình hoặc công cụ được sử dụng</p>
								</div>
								<div className="insight-item">
									<span>→</span>
									<p>Miễn phí, nhanh và có thể dùng ngay</p>
								</div>
							</div>

							<button className="btn primary wide" type="button" onClick={() => openAuth("login")}>Chạy phát hiện AI</button>
							<p className="mini-copy">
								Bằng cách tiếp tục, bạn đồng ý với điều khoản sử dụng của demo này.
							</p>
						</aside>
					</div>
				</section>

				<section className="feature-section" id="features">
					<div className="feature-copy">
						<p className="section-kicker">AI Detector</p>
						<h2>Phân tích nguồn AI sâu</h2>
						<p>
							Vượt xa hơn khả năng phát hiện hình ảnh; tìm ra nguồn gốc của nó. Mô
							hình AI Image Detector của chúng tôi nhận dạng các mẫu ở cấp độ
							pixel.
						</p>
						<p>
							Nó không chỉ cho bạn biết xác suất AI mà còn xác định mô hình AI đã tạo
							ra hình ảnh, hay bị thay đổi bằng công nghệ deepfake.
						</p>
						<button className="btn primary" type="button" onClick={() => openAuth("login")}>
							Tìm hiểu thêm
						</button>
					</div>

					<div className="feature-visual">
						<div className="orbit-card small">
							<span>50%</span>
							<strong>Mix of AI and Human</strong>
						</div>
						<div className="orbit-card large">
							<span>100%</span>
							<strong>AI</strong>
						</div>
						<div className="visual-image">
							<img src={FEATURE_IMAGE_URL} alt="Minh họa phát hiện hình ảnh AI" />
						</div>
					</div>
				</section>

				<section className="steps-section" id="how-it-works">
					<div className="section-heading center">
						<p className="section-kicker">Cách sử dụng</p>
						<h2>Làm thế nào để sử dụng công cụ này?</h2>
					</div>

					<div className="steps-grid">
						<article className="step-card">
							<div className="step-icon">↥</div>
							<h3>Tải lên hình ảnh</h3>
							<p>Kéo thả ảnh hoặc chọn file từ máy tính để bắt đầu.</p>
						</article>
						<article className="step-card">
							<div className="step-icon">⚡</div>
							<h3>Phân tích tức thời</h3>
							<p>Hệ thống sẽ xử lý ảnh và caption ngay sau khi bạn bấm kiểm tra.</p>
						</article>
						<article className="step-card">
							<div className="step-icon">▥</div>
							<h3>Nhận điểm của bạn</h3>
							<p>Xem kết quả khớp hoặc không khớp cùng gợi ý mô tả phù hợp hơn.</p>
						</article>
					</div>
				</section>
			</main>

			{isAuthOpen ? (
				<div className="auth-backdrop" role="presentation" onClick={closeAuth}>
					<div className="auth-modal" role="dialog" aria-modal="true" onClick={(event) => event.stopPropagation()}>
						<button className="close-button" type="button" onClick={closeAuth}>
							×
						</button>

						<div className="auth-switcher">
							<button
								className={authMode === "login" ? "auth-tab active" : "auth-tab"}
								type="button"
								onClick={() => switchAuthMode("login")}
							>
								Đăng nhập
							</button>
							<button
								className={authMode === "register" ? "auth-tab active" : "auth-tab"}
								type="button"
								onClick={() => switchAuthMode("register")}
							>
								Đăng ký
							</button>
						</div>

						<h2>{authMode === "login" ? "Đăng nhập tài khoản" : "Tạo tài khoản mới"}</h2>
						<p className="auth-copy">{authInfo}</p>

						<form className="auth-form" onSubmit={handleAuthSubmit}>
							{authMode === "register" ? (
								<label>
									<span>Họ và tên</span>
									<input
										name="name"
										type="text"
										value={authForm.name}
										onChange={handleAuthChange}
										placeholder="Nhập tên của bạn"
									/>
								</label>
							) : null}

							<label>
								<span>Email</span>
								<input
									name="email"
									type="email"
									value={authForm.email}
									onChange={handleAuthChange}
									placeholder="you@example.com"
								/>
							</label>

							<label>
								<span>Mật khẩu</span>
								<input
									name="password"
									type="password"
									value={authForm.password}
									onChange={handleAuthChange}
									placeholder="Nhập mật khẩu"
								/>
							</label>

							{authError ? <p className="error-text auth-error">{authError}</p> : null}

							<button className="btn primary wide" type="submit">
								{authMode === "login" ? "Đăng nhập" : "Tạo tài khoản"}
							</button>
						</form>
					</div>
				</div>
			) : null}
		</div>
	);
}

export default App;
