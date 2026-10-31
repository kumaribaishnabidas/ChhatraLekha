import SwiftUI

/// Clean, accessible sign-in screen supporting role selection and biometric unlock.
public struct LoginView: View {
    @ObservedObject var viewModel: AuthViewModel
    @State private var showForgotPassword = false

    public init(viewModel: AuthViewModel) {
        self.viewModel = viewModel
    }

    public var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {
                    // Header Brand Lockup
                    VStack(spacing: 8) {
                        Image(systemName: "graduationcap.fill")
                            .font(.system(size: 48))
                            .foregroundColor(.brandPrimary)
                            .padding(.top, 24)
                        Text("ChhatraLekha")
                            .font(.system(size: 28, weight: .black))
                            .foregroundColor(.inkPrimary)
                        Text("Unified Academic Operations & Identity Platform")
                            .font(.subheadline)
                            .foregroundColor(.inkMuted)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal, 16)
                    }

                    // Role Picker Segment
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Select Workspace Role")
                            .font(.caption.bold())
                            .foregroundColor(.inkMuted)
                            .textCase(.uppercase)

                        Picker("Workspace Role", selection: $viewModel.selectedRole) {
                            ForEach(UserRole.allCases) { role in
                                Text(role.displayName).tag(role)
                            }
                        }
                        .pickerStyle(MenuPickerStyle())
                        .padding(10)
                        .background(Color.surfaceBackground)
                        .cornerRadius(8)
                        .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.borderLine, lineWidth: 1))
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)

                    // Credentials Input
                    VStack(spacing: 16) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text("Email / Username")
                                .font(.caption.bold())
                                .foregroundColor(.inkMuted)
                            TextField("Enter your identifier", text: $viewModel.username)
                                .textInputAutocapitalization(.never)
                                .autocorrectionDisabled(true)
                                .padding(12)
                                .background(Color.surfaceBackground)
                                .cornerRadius(8)
                                .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.borderLine, lineWidth: 1))
                        }

                        VStack(alignment: .leading, spacing: 6) {
                            Text("Password")
                                .font(.caption.bold())
                                .foregroundColor(.inkMuted)
                            SecureField("Enter password", text: $viewModel.password)
                                .padding(12)
                                .background(Color.surfaceBackground)
                                .cornerRadius(8)
                                .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.borderLine, lineWidth: 1))
                        }
                    }

                    if let err = viewModel.errorMessage {
                        Text(err)
                            .font(.caption)
                            .foregroundColor(.errorCrimson)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    // Submit CTA
                    VStack(spacing: 12) {
                        PrimaryButton(
                            title: "Sign In to Workspace",
                            iconName: "arrow.right",
                            isLoading: viewModel.isLoading
                        ) {
                            Task {
                                await viewModel.login()
                            }
                        }

                        if BiometricManager.shared.biometricType != .none {
                            PrimaryButton(
                                title: "Unlock with Face ID / Touch ID",
                                iconName: "faceid",
                                isSecondary: true
                            ) {
                                Task {
                                    await viewModel.authenticateWithBiometrics()
                                }
                            }
                        }

                        Button(action: { showForgotPassword = true }) {
                            Text("Forgot password?")
                                .font(.subheadline)
                                .foregroundColor(.brandPrimary)
                        }
                        .padding(.top, 4)
                    }

                    // Notice / Governance
                    VStack(spacing: 4) {
                        Text("Demonstration prototype environment.")
                            .font(.caption2)
                            .foregroundColor(.inkMuted)
                        Text("Aligned with Digital Personal Data Protection Act 2023.")
                            .font(.caption2)
                            .foregroundColor(.inkMuted)
                    }
                    .padding(.top, 24)
                }
                .padding(24)
            }
            .sheet(isPresented: $showForgotPassword) {
                ForgotPasswordView()
            }
        }
    }
}

/// Reset password request flow.
public struct ForgotPasswordView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var email: String = ""
    @State private var submitted: Bool = false

    public var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                Image(systemName: "key.fill")
                    .font(.system(size: 40))
                    .foregroundColor(.brandPrimary)
                    .padding(.top, 20)
                Text("Password Recovery")
                    .font(.title2.bold())
                Text("Enter your registered academic institution email address to receive password reset instructions.")
                    .font(.subheadline)
                    .foregroundColor(.inkMuted)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 24)

                if submitted {
                    Text("If an account exists for \(email), instructions have been dispatched.")
                        .font(.callout)
                        .foregroundColor(.successGreen)
                        .padding()
                        .background(Color.successGreen.opacity(0.1))
                        .cornerRadius(8)
                } else {
                    TextField("Academic email address", text: $email)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled(true)
                        .padding(12)
                        .background(Color.surfaceBackground)
                        .cornerRadius(8)
                        .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.borderLine, lineWidth: 1))
                        .padding(.horizontal, 24)

                    PrimaryButton(title: "Send Reset Link") {
                        submitted = true
                    }
                    .padding(.horizontal, 24)
                }

                Spacer()
            }
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                }
            }
        }
    }
}

